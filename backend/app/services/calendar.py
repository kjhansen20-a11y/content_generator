import json
from datetime import datetime

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models.content import (
    CalendarItemStatus,
    ContentCalendarItem,
    GeneratedPost,
    PostVersion,
)
from app.schemas.content import CalendarItemContentUpdate, CalendarItemRead, GeneratedPostContent
from app.services.generation import _parse_content, _to_calendar_item_read


def _get_item_with_post(
    session: Session,
    company_id: int,
    item_id: int,
) -> tuple[ContentCalendarItem, GeneratedPost]:
    row = session.exec(
        select(ContentCalendarItem, GeneratedPost)
        .join(GeneratedPost, GeneratedPost.id == ContentCalendarItem.generated_post_id)
        .where(
            ContentCalendarItem.id == item_id,
            ContentCalendarItem.company_id == company_id,
        )
    ).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar item not found")
    return row


def _require_status(item: ContentCalendarItem, allowed: set[CalendarItemStatus], action: str) -> None:
    if item.status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot {action} while status is '{item.status.value}'",
        )


def update_calendar_item(
    session: Session,
    company_id: int,
    item_id: int,
    payload: CalendarItemContentUpdate,
) -> CalendarItemRead:
    item, post = _get_item_with_post(session, company_id, item_id)
    _require_status(item, {CalendarItemStatus.draft}, "edit")

    session.add(
        PostVersion(
            generated_post_id=post.id,
            content_json=post.content_json,
        )
    )

    existing = _parse_content(json.loads(post.content_json))
    updated = GeneratedPostContent(
        hook=payload.hook.strip(),
        body=payload.body.strip(),
        hashtags=[h.lstrip("#").strip() for h in payload.hashtags if h.strip()],
        platform=existing.platform,
        post_type=existing.post_type,
        alt_text=payload.alt_text,
        quality_notes=existing.quality_notes,
        compliance_notes=existing.compliance_notes,
        suggested_publish_time=payload.suggested_publish_time,
    )

    post.content_json = updated.model_dump_json()
    item.hook_preview = updated.hook[:500]
    item.scheduled_date = payload.scheduled_date
    item.scheduled_time = payload.scheduled_time
    item.updated_at = datetime.utcnow()

    session.add(post)
    session.add(item)
    session.commit()
    session.refresh(item)
    session.refresh(post)
    return _to_calendar_item_read(item, post)


def approve_calendar_item(session: Session, company_id: int, item_id: int) -> CalendarItemRead:
    item, post = _get_item_with_post(session, company_id, item_id)
    _require_status(item, {CalendarItemStatus.draft}, "approve")

    item.status = CalendarItemStatus.approved
    item.updated_at = datetime.utcnow()
    session.add(item)
    session.commit()
    session.refresh(item)
    return _to_calendar_item_read(item, post)


def queue_calendar_item(session: Session, company_id: int, item_id: int) -> CalendarItemRead:
    item, post = _get_item_with_post(session, company_id, item_id)
    _require_status(item, {CalendarItemStatus.approved}, "queue")

    item.status = CalendarItemStatus.queued
    item.updated_at = datetime.utcnow()
    session.add(item)
    session.commit()
    session.refresh(item)
    return _to_calendar_item_read(item, post)
