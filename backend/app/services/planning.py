from datetime import date, datetime, timedelta

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models.content import Platform, PostType
from app.models.planning import (
    ContentPillar,
    MarketingPlan,
    MarketingPlanStatus,
    PostingFrequency,
    PostingRule,
)
from app.models.tenancy import Company
from app.schemas.planning import (
    ContentPillarCreate,
    ContentPillarRead,
    ContentPillarUpdate,
    GenerateMarketingPlanRequest,
    GenerateMarketingPlanResponse,
    MarketingPlanCreate,
    MarketingPlanRead,
    MarketingPlanUpdate,
    PostingRuleCreate,
    PostingRuleRead,
    PostingRuleUpdate,
)
from app.services.openai_client import chat_json
from app.services.plan_builder import (
    build_marketing_plan_import_user,
    build_marketing_plan_system,
    build_marketing_plan_user,
)
from app.services.optimal_posting_times import optimal_time_for_slot
from app.services.text_extract import ALLOWED_PLAN_EXTENSIONS, extract_text_from_bytes

WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def get_active_marketing_plan(session: Session, company_id: int) -> MarketingPlan | None:
    return session.exec(
        select(MarketingPlan)
        .where(
            MarketingPlan.company_id == company_id,
            MarketingPlan.status == MarketingPlanStatus.active,
        )
        .order_by(MarketingPlan.updated_at.desc())
    ).first()


def list_marketing_plans(session: Session, company_id: int) -> list[MarketingPlan]:
    return list(
        session.exec(
            select(MarketingPlan)
            .where(MarketingPlan.company_id == company_id)
            .order_by(MarketingPlan.updated_at.desc())
        ).all()
    )


def create_marketing_plan(
    session: Session, company_id: int, payload: MarketingPlanCreate
) -> MarketingPlan:
    plan = MarketingPlan(company_id=company_id, **payload.model_dump())
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return plan


def update_marketing_plan(
    session: Session, company_id: int, plan_id: int, payload: MarketingPlanUpdate
) -> MarketingPlan:
    plan = session.get(MarketingPlan, plan_id)
    if plan is None or plan.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Marketing plan not found")

    data = payload.model_dump(exclude_unset=True)
    if data.get("status") == MarketingPlanStatus.active:
        for other in session.exec(
            select(MarketingPlan).where(
                MarketingPlan.company_id == company_id,
                MarketingPlan.status == MarketingPlanStatus.active,
                MarketingPlan.id != plan_id,
            )
        ).all():
            other.status = MarketingPlanStatus.archived
            other.updated_at = datetime.utcnow()
            session.add(other)

    for key, value in data.items():
        setattr(plan, key, value)
    plan.updated_at = datetime.utcnow()
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return plan


def delete_marketing_plan(session: Session, company_id: int, plan_id: int) -> None:
    plan = session.get(MarketingPlan, plan_id)
    if plan is None or plan.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Marketing plan not found")
    session.delete(plan)
    session.commit()


def list_content_pillars(session: Session, company_id: int) -> list[ContentPillar]:
    return list(
        session.exec(
            select(ContentPillar)
            .where(ContentPillar.company_id == company_id)
            .order_by(ContentPillar.weight.desc(), ContentPillar.name)
        ).all()
    )


def create_content_pillar(
    session: Session, company_id: int, payload: ContentPillarCreate
) -> ContentPillar:
    if payload.marketing_plan_id is not None:
        plan = session.get(MarketingPlan, payload.marketing_plan_id)
        if plan is None or plan.company_id != company_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid marketing plan")
    pillar = ContentPillar(company_id=company_id, **payload.model_dump())
    session.add(pillar)
    session.commit()
    session.refresh(pillar)
    return pillar


def update_content_pillar(
    session: Session, company_id: int, pillar_id: int, payload: ContentPillarUpdate
) -> ContentPillar:
    pillar = session.get(ContentPillar, pillar_id)
    if pillar is None or pillar.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content pillar not found")
    data = payload.model_dump(exclude_unset=True)
    if data.get("marketing_plan_id") is not None:
        plan = session.get(MarketingPlan, data["marketing_plan_id"])
        if plan is None or plan.company_id != company_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid marketing plan")
    for key, value in data.items():
        setattr(pillar, key, value)
    pillar.updated_at = datetime.utcnow()
    session.add(pillar)
    session.commit()
    session.refresh(pillar)
    return pillar


def delete_content_pillar(session: Session, company_id: int, pillar_id: int) -> None:
    pillar = session.get(ContentPillar, pillar_id)
    if pillar is None or pillar.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content pillar not found")
    session.delete(pillar)
    session.commit()


def list_posting_rules(session: Session, company_id: int) -> list[PostingRule]:
    return list(
        session.exec(
            select(PostingRule)
            .where(PostingRule.company_id == company_id)
            .order_by(PostingRule.weekday, PostingRule.post_time)
        ).all()
    )


def create_posting_rule(
    session: Session, company_id: int, payload: PostingRuleCreate
) -> PostingRule:
    rule = PostingRule(company_id=company_id, **payload.model_dump())
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return rule


def update_posting_rule(
    session: Session, company_id: int, rule_id: int, payload: PostingRuleUpdate
) -> PostingRule:
    rule = session.get(PostingRule, rule_id)
    if rule is None or rule.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Posting rule not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, key, value)
    rule.updated_at = datetime.utcnow()
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return rule


def delete_posting_rule(session: Session, company_id: int, rule_id: int) -> None:
    rule = session.get(PostingRule, rule_id)
    if rule is None or rule.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Posting rule not found")
    session.delete(rule)
    session.commit()


def planning_context_block(session: Session, company_id: int) -> str:
    sections: list[str] = []

    plan = get_active_marketing_plan(session, company_id)
    if plan:
        parts = [f"Active marketing plan: {plan.name}"]
        if plan.period_start or plan.period_end:
            parts.append(
                f"Period: {plan.period_start or '?'} to {plan.period_end or '?'}"
            )
        if plan.goals:
            parts.append(f"Goals: {plan.goals}")
        if plan.notes:
            parts.append(f"Plan notes: {plan.notes}")
        sections.append("\n".join(parts))

    pillars = list_content_pillars(session, company_id)
    if pillars:
        lines = ["Content pillars (higher weight = more focus):"]
        for pillar in pillars:
            desc = f" — {pillar.description}" if pillar.description else ""
            lines.append(f"- {pillar.name} (weight {pillar.weight}){desc}")
        sections.append("\n".join(lines))

    rules = [r for r in list_posting_rules(session, company_id) if r.is_active]
    if rules:
        lines = ["Posting schedule:"]
        for rule in rules:
            day = WEEKDAY_NAMES[rule.weekday]
            lines.append(
                f"- {rule.platform.value} · {day} at {rule.post_time} · "
                f"{rule.post_type.value} · {rule.frequency.value}"
            )
            if rule.notes:
                lines.append(f"  Note: {rule.notes}")
        sections.append("\n".join(lines))

    return "\n\n".join(sections)


def _parse_plan_content(data: dict) -> dict:
    pillars_raw = data.get("pillars") or []
    rules_raw = data.get("posting_rules") or []
    pillars: list[dict] = []
    for item in pillars_raw:
        if not isinstance(item, dict) or not item.get("name"):
            continue
        weight = item.get("weight", 5)
        try:
            weight = max(1, min(10, int(weight)))
        except (TypeError, ValueError):
            weight = 5
        pillars.append(
            {
                "name": str(item["name"]).strip()[:255],
                "description": str(item.get("description") or "").strip() or None,
                "weight": weight,
            }
        )
    rules: list[dict] = []
    for item in rules_raw:
        if not isinstance(item, dict):
            continue
        try:
            platform = Platform(str(item.get("platform", "linkedin")).lower())
            post_type = PostType(str(item.get("post_type", "professional")).lower())
            frequency = PostingFrequency(str(item.get("frequency", "weekly")).lower())
            weekday = int(item.get("weekday", 0))
            weekday = max(0, min(6, weekday))
        except (ValueError, TypeError):
            continue
        rules.append(
            {
                "platform": platform,
                "weekday": weekday,
                "post_time": str(item.get("post_time") or "09:00")[:8],
                "post_type": post_type,
                "frequency": frequency,
                "notes": str(item.get("notes") or "").strip()[:500] or None,
                "pillar_name": str(item.get("pillar") or "").strip() or None,
            }
        )
    return {
        "name": str(data.get("name") or "Marketing Plan").strip()[:255],
        "summary": str(data.get("summary") or "").strip(),
        "goals": str(data.get("goals") or "").strip(),
        "pillars": pillars,
        "posting_rules": rules,
    }


def _enforce_posts_per_week(rules: list[dict], limit: int) -> list[dict]:
    """Trim posting rules to the requested weekly total (across all platforms)."""
    if len(rules) <= limit:
        return rules
    sorted_rules = sorted(rules, key=lambda r: (r["weekday"], r["platform"].value))
    return sorted_rules[:limit]


def _apply_optimal_post_times(rules: list[dict]) -> list[dict]:
    """Snap each rule's post_time to the optimal window for its platform and weekday."""
    for rule in rules:
        rule["post_time"] = optimal_time_for_slot(rule["platform"], rule["weekday"])
    return rules


def _replace_active_plan_data(session: Session, company_id: int) -> None:
    for other in session.exec(
        select(MarketingPlan).where(
            MarketingPlan.company_id == company_id,
            MarketingPlan.status == MarketingPlanStatus.active,
        )
    ).all():
        other.status = MarketingPlanStatus.archived
        other.updated_at = datetime.utcnow()
        session.add(other)
    for pillar in list_content_pillars(session, company_id):
        session.delete(pillar)
    for rule in list_posting_rules(session, company_id):
        session.delete(rule)
    session.flush()


def _persist_parsed_plan(
    session: Session,
    company_id: int,
    parsed: dict,
    *,
    plan_name: str | None,
    notes: str,
    period_weeks: int | None = None,
) -> GenerateMarketingPlanResponse:
    period_start = date.today()
    period_end = period_start + timedelta(weeks=period_weeks) if period_weeks else None

    resolved_name = (plan_name.strip() if plan_name else None) or parsed["name"]
    plan = MarketingPlan(
        company_id=company_id,
        name=resolved_name,
        period_start=period_start,
        period_end=period_end,
        status=MarketingPlanStatus.active,
        goals=parsed["goals"] or None,
        notes=notes or None,
    )
    session.add(plan)
    session.flush()

    created_pillars: list[ContentPillar] = []
    for pillar_data in parsed["pillars"]:
        pillar = ContentPillar(
            company_id=company_id,
            marketing_plan_id=plan.id,
            name=pillar_data["name"],
            description=pillar_data.get("description"),
            weight=pillar_data.get("weight", 5),
        )
        session.add(pillar)
        created_pillars.append(pillar)
    session.flush()

    pillar_by_name = {p.name.lower(): p.id for p in created_pillars}

    created_rules: list[PostingRule] = []
    for rule_data in parsed["posting_rules"]:
        data = dict(rule_data)
        pillar_name = (data.pop("pillar_name", None) or "").lower()
        pillar_id = pillar_by_name.get(pillar_name) if pillar_name else None
        data.pop("pillar_name", None)
        rule = PostingRule(company_id=company_id, content_pillar_id=pillar_id, **data)
        session.add(rule)
        created_rules.append(rule)

    session.commit()
    session.refresh(plan)
    for pillar in created_pillars:
        session.refresh(pillar)
    for rule in created_rules:
        session.refresh(rule)

    return GenerateMarketingPlanResponse(
        plan=MarketingPlanRead.model_validate(plan),
        pillars=[ContentPillarRead.model_validate(p) for p in created_pillars],
        posting_rules=[PostingRuleRead.model_validate(r) for r in created_rules],
    )


def generate_marketing_plan_with_ai(
    session: Session,
    company: Company,
    request: GenerateMarketingPlanRequest,
) -> GenerateMarketingPlanResponse:
    system_prompt = build_marketing_plan_system(session)
    user_prompt = build_marketing_plan_user(session, company, request)

    result = chat_json(
        session,
        company_id=company.id,
        operation="generate_marketing_plan",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    parsed = _parse_plan_content(result.content)
    if not parsed["goals"] and not parsed["pillars"]:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI returned an incomplete marketing plan. Try different keywords or expectations.",
        )

    parsed["posting_rules"] = _enforce_posts_per_week(
        parsed["posting_rules"], request.posts_per_week
    )
    parsed["posting_rules"] = _apply_optimal_post_times(parsed["posting_rules"])

    if request.replace_existing:
        _replace_active_plan_data(session, company.id)

    notes_parts = []
    if parsed["summary"]:
        notes_parts.append(parsed["summary"])
    expectations = (request.plan_expectations or "").strip()
    if expectations:
        notes_parts.append(f"Plan expectations:\n{expectations}")
    keywords = request.keywords.strip()
    if keywords:
        notes_parts.append(f"Keywords: {keywords}")
    notes = "\n\n".join(notes_parts)

    return _persist_parsed_plan(
        session,
        company.id,
        parsed,
        plan_name=request.plan_name.strip() if request.plan_name else None,
        notes=notes,
        period_weeks=request.period_weeks,
    )


def import_marketing_plan_from_document(
    session: Session,
    company: Company,
    *,
    filename: str,
    file_bytes: bytes,
    mime_type: str | None,
    plan_name: str | None,
    replace_existing: bool,
) -> GenerateMarketingPlanResponse:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_PLAN_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Use: {', '.join(sorted(ALLOWED_PLAN_EXTENSIONS))}",
        )

    try:
        document_text = extract_text_from_bytes(filename, file_bytes, mime_type)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    system_prompt = build_marketing_plan_system(session)
    user_prompt = build_marketing_plan_import_user(
        session,
        company,
        document_text,
        plan_name,
    )

    result = chat_json(
        session,
        company_id=company.id,
        operation="import_marketing_plan",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    parsed = _parse_plan_content(result.content)
    if not parsed["goals"] and not parsed["pillars"]:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not structure a marketing plan from this document. Try a clearer source file.",
        )

    parsed["posting_rules"] = _apply_optimal_post_times(parsed["posting_rules"])

    if replace_existing:
        _replace_active_plan_data(session, company.id)

    notes_parts = []
    if parsed["summary"]:
        notes_parts.append(parsed["summary"])
    notes_parts.append(f"Imported from {filename}")
    notes = "\n\n".join(notes_parts)

    return _persist_parsed_plan(
        session,
        company.id,
        parsed,
        plan_name=plan_name.strip() if plan_name else None,
        notes=notes,
        period_weeks=12,
    )
