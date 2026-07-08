from dataclasses import dataclass
from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models.content import CalendarItemStatus, ContentCalendarItem, FILLED_SLOT_STATUSES, Platform, PostType
from app.models.planning import ContentPillar, PostingFrequency, PostingRule

_FILLED = list(FILLED_SLOT_STATUSES)


@dataclass
class SlotInfo:
    rule_id: int
    platform: Platform
    post_type: PostType
    weekday: int
    post_time: str
    target_date: date
    pillar_id: int | None
    pillar_name: str | None
    filled: bool
    calendar_item_id: int | None = None
    hook_preview: str | None = None
    status: str | None = None


def week_bounds(anchor: date) -> tuple[date, date]:
    monday = anchor - timedelta(days=anchor.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def _target_date_for_rule(rule: PostingRule, week_monday: date) -> date:
    return week_monday + timedelta(days=rule.weekday)


def _slot_filled_between(
    session: Session,
    company_id: int,
    rule_id: int,
    start: date,
    end: date,
) -> bool:
    item = session.exec(
        select(ContentCalendarItem).where(
            ContentCalendarItem.company_id == company_id,
            ContentCalendarItem.posting_rule_id == rule_id,
            ContentCalendarItem.scheduled_date >= start,
            ContentCalendarItem.scheduled_date <= end,
            ContentCalendarItem.status.in_(_FILLED),
        )
    ).first()
    return item is not None


def _frequency_allows_slot(
    session: Session,
    company_id: int,
    rule: PostingRule,
    target_date: date,
) -> bool:
    if rule.frequency in (PostingFrequency.weekly, PostingFrequency.daily):
        return True
    if rule.frequency == PostingFrequency.biweekly:
        prev_week_start = target_date - timedelta(days=target_date.weekday() + 7)
        prev_week_end = prev_week_start + timedelta(days=6)
        return not _slot_filled_between(session, company_id, rule.id, prev_week_start, prev_week_end)
    if rule.frequency == PostingFrequency.monthly:
        month_start = target_date.replace(day=1)
        if target_date.month == 12:
            month_end = date(target_date.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(target_date.year, target_date.month + 1, 1) - timedelta(days=1)
        return not _slot_filled_between(session, company_id, rule.id, month_start, month_end)
    return True


def _get_filled_item(
    session: Session,
    company_id: int,
    rule: PostingRule,
    target: date,
) -> ContentCalendarItem | None:
    item = session.exec(
        select(ContentCalendarItem).where(
            ContentCalendarItem.company_id == company_id,
            ContentCalendarItem.posting_rule_id == rule.id,
            ContentCalendarItem.scheduled_date == target,
            ContentCalendarItem.status.in_(_FILLED),
        )
    ).first()
    if item:
        return item
    return session.exec(
        select(ContentCalendarItem).where(
            ContentCalendarItem.company_id == company_id,
            ContentCalendarItem.posting_rule_id.is_(None),
            ContentCalendarItem.platform == rule.platform,
            ContentCalendarItem.scheduled_date == target,
            ContentCalendarItem.status.in_(_FILLED),
        )
    ).first()


def _pillar_for_rule(session: Session, rule: PostingRule) -> tuple[int | None, str | None]:
    if rule.content_pillar_id:
        pillar = session.get(ContentPillar, rule.content_pillar_id)
        if pillar:
            return pillar.id, pillar.name
    return None, None


def list_week_slots(session: Session, company_id: int, week_anchor: date) -> list[SlotInfo]:
    week_monday, week_sunday = week_bounds(week_anchor)
    rules = list(
        session.exec(
            select(PostingRule)
            .where(PostingRule.company_id == company_id, PostingRule.is_active == True)  # noqa: E712
            .order_by(PostingRule.weekday, PostingRule.post_time)
        ).all()
    )
    slots: list[SlotInfo] = []
    for rule in rules:
        target = _target_date_for_rule(rule, week_monday)
        if target < week_monday or target > week_sunday:
            continue
        if not _frequency_allows_slot(session, company_id, rule, target):
            continue
        filled_item = _get_filled_item(session, company_id, rule, target)
        pillar_id, pillar_name = _pillar_for_rule(session, rule)
        slots.append(
            SlotInfo(
                rule_id=rule.id,
                platform=rule.platform,
                post_type=rule.post_type,
                weekday=rule.weekday,
                post_time=rule.post_time,
                target_date=target,
                pillar_id=pillar_id,
                pillar_name=pillar_name,
                filled=filled_item is not None,
                calendar_item_id=filled_item.id if filled_item else None,
                hook_preview=filled_item.hook_preview if filled_item else None,
                status=filled_item.status.value if filled_item else None,
            )
        )
    slots.sort(key=lambda s: (s.target_date, s.post_time))
    return slots


def get_next_empty_slot(
    session: Session,
    company_id: int,
    from_date: date | None = None,
    *,
    allow_next_week: bool = False,
) -> SlotInfo | None:
    anchor = from_date or date.today()
    week_monday, _ = week_bounds(anchor)

    for week_offset in range(2 if allow_next_week else 1):
        check_monday = week_monday + timedelta(weeks=week_offset)
        for slot in list_week_slots(session, company_id, check_monday):
            if slot.target_date < anchor and week_offset == 0:
                continue
            if not slot.filled:
                return slot
    return None


def resolve_follow_plan_slot(
    session: Session,
    company_id: int,
    from_date: date | None = None,
    use_next_week: bool = False,
) -> SlotInfo:
    has_rules = session.exec(
        select(PostingRule).where(PostingRule.company_id == company_id, PostingRule.is_active == True)  # noqa: E712
    ).first()
    if has_rules is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active posting rules. Create a marketing plan first.",
        )

    anchor = from_date or date.today()
    slot = get_next_empty_slot(session, company_id, anchor, allow_next_week=use_next_week)
    if slot is None:
        if not use_next_week:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="all_slots_filled_this_week",
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="All plan slots are filled for the next two weeks.",
        )
    return slot
