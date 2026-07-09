import json
from datetime import date, datetime

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models.content import (
    CalendarItemStatus,
    ContentCalendarItem,
    GenerateMode,
    GeneratedPost,
    Platform,
    PostType,
    PUBLISHABLE_PLATFORMS,
)
from app.models.knowledge import FileKind
from app.models.planning import ContentPillar
from app.models.tenancy import Company
from app.schemas.content import (
    CalendarItemRead,
    GeneratePostRequest,
    GeneratePostResponse,
    GeneratedPostContent,
    GeneratedPostRead,
    WeekSlotRead,
    WeekSlotsResponse,
)
from app.services.files import get_uploaded_file
from app.services.openai_client import chat_json
from app.services.post_language import (
    build_language_preservation_instruction,
    build_post_language_instruction,
    resolve_output_language,
    user_language_source,
)
from app.services.prompt_builder import (
    ResolvedPostContext,
    build_brief_user_prompt,
    build_system_prompt,
    build_user_prompt,
    get_active_prompt_body,
    get_active_prompt_version_id,
)
from app.services.slot_resolver import SlotInfo, list_week_slots, resolve_follow_plan_slot, week_bounds

WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _parse_content(data: dict) -> GeneratedPostContent:
    hashtags = data.get("hashtags") or []
    if isinstance(hashtags, str):
        hashtags = [h.strip() for h in hashtags.split(",") if h.strip()]
    return GeneratedPostContent(
        hook=str(data.get("hook", "")).strip(),
        body=str(data.get("body", "")).strip(),
        hashtags=[str(h).lstrip("#") for h in hashtags],
        platform=str(data.get("platform", "")),
        post_type=str(data.get("post_type", "")),
        alt_text=data.get("alt_text"),
        quality_notes=data.get("quality_notes"),
        compliance_notes=data.get("compliance_notes"),
        suggested_publish_time=data.get("suggested_publish_time"),
    )


def _to_generated_post_read(post: GeneratedPost) -> GeneratedPostRead:
    content = _parse_content(json.loads(post.content_json))
    return GeneratedPostRead(
        id=post.id,
        company_id=post.company_id,
        platform=post.platform,
        post_type=post.post_type,
        content=content,
        model=post.model,
        created_at=post.created_at,
    )


def _to_calendar_item_read(item: ContentCalendarItem, post: GeneratedPost) -> CalendarItemRead:
    content = _parse_content(json.loads(post.content_json))
    return CalendarItemRead(
        id=item.id,
        company_id=item.company_id,
        generated_post_id=item.generated_post_id,
        scheduled_date=item.scheduled_date,
        scheduled_time=item.scheduled_time,
        posting_rule_id=item.posting_rule_id,
        content_pillar_id=item.content_pillar_id,
        platform=item.platform,
        post_type=item.post_type,
        status=item.status,
        hook_preview=item.hook_preview,
        image_file_id=post.image_file_id,
        content=content,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _slot_label(slot: SlotInfo) -> str:
    day = WEEKDAY_NAMES[slot.weekday]
    pillar = f" · {slot.pillar_name}" if slot.pillar_name else ""
    return f"{slot.platform.value.title()} · {day} {slot.post_time}{pillar}"


def _pillar_description(session: Session, pillar_id: int | None) -> str | None:
    if not pillar_id:
        return None
    pillar = session.get(ContentPillar, pillar_id)
    return pillar.description if pillar else None


def _lock_content_platform(
    content: GeneratedPostContent,
    platform: Platform,
    post_type: PostType,
) -> GeneratedPostContent:
    return content.model_copy(
        update={"platform": platform.value, "post_type": post_type.value},
    )


def _resolve_generation(
    session: Session,
    company_id: int,
    request: GeneratePostRequest,
) -> tuple[ResolvedPostContext, Platform, PostType, date | None, str | None, int | None, int | None, str | None]:
    """Returns context, platform, post_type, scheduled_date iso, scheduled_time, rule_id, pillar_id, slot_label."""
    language_source = user_language_source(request.content_idea, request.keywords)
    output_language = resolve_output_language(request.output_language, language_source)
    if request.mode == GenerateMode.instant:
        assert request.platform and request.post_type
        idea = (request.content_idea or "").strip() or "Create an engaging on-brand post for this company."
        ctx = ResolvedPostContext(
            platform=request.platform,
            post_type=request.post_type,
            content_idea=idea,
            include_planning=False,
            language_source=language_source,
            output_language=output_language,
        )
        return ctx, request.platform, request.post_type, None, None, None, None, None

    if request.mode == GenerateMode.scheduled_manual:
        assert request.platform and request.post_type and request.scheduled_date
        idea = (request.content_idea or "").strip() or "Create an engaging on-brand post for this company."
        ctx = ResolvedPostContext(
            platform=request.platform,
            post_type=request.post_type,
            content_idea=idea,
            include_planning=False,
            language_source=language_source,
            output_language=output_language,
        )
        sched_time = request.scheduled_time
        return (
            ctx,
            request.platform,
            request.post_type,
            request.scheduled_date,
            sched_time,
            None,
            None,
            None,
        )

    slot = resolve_follow_plan_slot(
        session,
        company_id,
        use_next_week=request.use_next_week,
    )
    if slot.platform not in PUBLISHABLE_PLATFORMS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Your next marketing plan slot is {slot.platform.value.title()}, which is not "
                "supported for publishing yet. Update your plan to use LinkedIn or Facebook."
            ),
        )
    label = _slot_label(slot)
    idea = (request.content_idea or "").strip()
    pillar_desc = _pillar_description(session, slot.pillar_id)
    ctx = ResolvedPostContext(
        platform=slot.platform,
        post_type=slot.post_type,
        content_idea=idea,
        include_planning=True,
        language_source=language_source,
        output_language=output_language,
        pillar_name=slot.pillar_name,
        pillar_description=pillar_desc,
        slot_label=label,
    )
    return (
        ctx,
        slot.platform,
        slot.post_type,
        slot.target_date,
        slot.post_time,
        slot.rule_id,
        slot.pillar_id,
        label,
    )


def _run_brief(session: Session, company: Company, ctx: ResolvedPostContext) -> str:
    if ctx.content_idea.strip():
        return ctx.content_idea.strip()
    try:
        brief_system = get_active_prompt_body(session, "post_brief")
    except ValueError:
        return "Create an engaging on-brand post aligned with the company and content pillar."
    result = chat_json(
        session,
        company_id=company.id,
        operation="post_brief",
        system_prompt=brief_system,
        user_prompt=build_brief_user_prompt(session, company, ctx),
    )
    brief = str(result.content.get("brief", "")).strip()
    return brief or "Create an engaging on-brand post."


def get_week_slots(session: Session, company_id: int, week_anchor: date | None = None) -> WeekSlotsResponse:
    anchor = week_anchor or date.today()
    week_start, week_end = week_bounds(anchor)
    slots = list_week_slots(session, company_id, anchor)
    return WeekSlotsResponse(
        week_start=week_start,
        week_end=week_end,
        slots=[WeekSlotRead.model_validate(s.__dict__) for s in slots],
        all_filled=bool(slots) and all(s.filled for s in slots),
    )


def generate_post(
    session: Session,
    company: Company,
    request: GeneratePostRequest,
) -> GeneratePostResponse:
    if request.image_file_id:
        image_file = get_uploaded_file(session, company.id, request.image_file_id)
        if image_file.kind != FileKind.post_image:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="image_file_id must reference a post image upload",
            )

    ctx, platform, post_type, scheduled_date, sched_time, rule_id, pillar_id, slot_label = _resolve_generation(
        session, company.id, request
    )

    brief = _run_brief(session, company, ctx)
    ctx.content_idea = brief

    language_instruction = build_post_language_instruction(ctx.output_language, ctx.language_source)
    preserve_language = build_language_preservation_instruction(ctx.output_language)

    system_prompt = language_instruction + "\n\n" + build_system_prompt(session, post_type, platform)
    user_prompt = build_user_prompt(session, company, request, ctx)
    base_version_id = get_active_prompt_version_id(session, "base")

    draft_result = chat_json(
        session,
        company_id=company.id,
        operation="generate_post",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )
    content = _parse_content(draft_result.content)

    quality_system = get_active_prompt_body(session, "quality_check")
    quality_result = chat_json(
        session,
        company_id=company.id,
        operation="quality_check",
        system_prompt=quality_system,
        user_prompt=preserve_language + "\n\n" + json.dumps(draft_result.content, ensure_ascii=False),
    )
    reviewed = _parse_content(quality_result.content)

    try:
        revise_system = get_active_prompt_body(session, "post_revise")
        revise_payload = {
            "draft": draft_result.content,
            "quality_notes": reviewed.quality_notes,
            "compliance_notes": reviewed.compliance_notes,
        }
        revise_result = chat_json(
            session,
            company_id=company.id,
            operation="post_revise",
            system_prompt=revise_system,
            user_prompt=preserve_language + "\n\n" + json.dumps(revise_payload, ensure_ascii=False),
        )
        revised = _parse_content(revise_result.content)
        if revised.hook and revised.body:
            content = revised
            content.quality_notes = reviewed.quality_notes
            content.compliance_notes = reviewed.compliance_notes
    except ValueError:
        content.quality_notes = reviewed.quality_notes or content.quality_notes
        content.compliance_notes = reviewed.compliance_notes or content.compliance_notes

    if not content.hook or not content.body:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Generated post is missing required fields (hook/body)",
        )

    content = _lock_content_platform(content, platform, post_type)

    generated_post = GeneratedPost(
        company_id=company.id,
        platform=platform,
        post_type=post_type,
        content_json=content.model_dump_json(),
        model=draft_result.model,
        prompt_version_id=base_version_id,
        image_file_id=request.image_file_id,
    )
    session.add(generated_post)
    session.flush()

    calendar_item = ContentCalendarItem(
        company_id=company.id,
        generated_post_id=generated_post.id,
        scheduled_date=scheduled_date,
        scheduled_time=sched_time,
        posting_rule_id=rule_id,
        content_pillar_id=pillar_id,
        platform=platform,
        post_type=post_type,
        status=CalendarItemStatus.draft,
        hook_preview=content.hook[:500],
        updated_at=datetime.utcnow(),
    )
    session.add(calendar_item)
    session.commit()
    session.refresh(generated_post)
    session.refresh(calendar_item)

    return GeneratePostResponse(
        generated_post=_to_generated_post_read(generated_post),
        calendar_item=_to_calendar_item_read(calendar_item, generated_post),
        slot_label=slot_label,
    )


def list_calendar_items(session: Session, company_id: int) -> list[CalendarItemRead]:
    rows = session.exec(
        select(ContentCalendarItem, GeneratedPost)
        .join(GeneratedPost, GeneratedPost.id == ContentCalendarItem.generated_post_id)
        .where(ContentCalendarItem.company_id == company_id)
        .order_by(ContentCalendarItem.created_at.desc())
    ).all()
    return [_to_calendar_item_read(item, post) for item, post in rows]
