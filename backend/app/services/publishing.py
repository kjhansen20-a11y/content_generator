import json
import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models.auth import User
from app.models.content import CalendarItemStatus, ContentCalendarItem, GeneratedPost, Platform
from app.models.publishing import (
    AccountStatus,
    ConnectedAccount,
    PublishingJob,
    PublishingJobStatus,
)
from app.schemas.publishing import (
    ConnectedAccountRead,
    PublishResponse,
    PublishingJobRead,
    QueueItemRead,
)
from app.services.generation import _parse_content, _to_calendar_item_read


MOCK_ACCOUNT_NAMES = {
    Platform.linkedin: "Mock LinkedIn Company Page",
    Platform.facebook: "Mock Facebook Page",
    Platform.instagram: "Mock Instagram Business",
}


def _get_mock_account(session: Session, company_id: int, platform: Platform) -> ConnectedAccount:
    account = session.exec(
        select(ConnectedAccount).where(
            ConnectedAccount.company_id == company_id,
            ConnectedAccount.platform == platform,
            ConnectedAccount.is_mock == True,  # noqa: E712
        )
    ).first()
    if account is None:
        account = ConnectedAccount(
            company_id=company_id,
            platform=platform,
            account_name=MOCK_ACCOUNT_NAMES[platform],
            is_mock=True,
            status=AccountStatus.active,
        )
        session.add(account)
        session.flush()
    return account


def _job_to_read(
    job: PublishingJob,
    item: ContentCalendarItem | None = None,
    post: GeneratedPost | None = None,
) -> PublishingJobRead:
    content = None
    image_file_id = None
    if post is not None:
        content = _parse_content(json.loads(post.content_json))
        image_file_id = post.image_file_id
    return PublishingJobRead(
        id=job.id,
        company_id=job.company_id,
        calendar_item_id=job.calendar_item_id,
        connected_account_id=job.connected_account_id,
        status=job.status,
        attempts=job.attempts,
        result_message=job.result_message,
        error_message=job.error_message,
        external_post_id=job.external_post_id,
        created_at=job.created_at,
        completed_at=job.completed_at,
        hook_preview=item.hook_preview if item else None,
        platform=item.platform if item else None,
        image_file_id=image_file_id,
        content=content,
    )


def connected_account_to_read(session: Session, account: ConnectedAccount) -> ConnectedAccountRead:
    email = None
    if account.connected_by_user_id:
        user = session.get(User, account.connected_by_user_id)
        email = user.email if user else None
    data = ConnectedAccountRead.model_validate(account)
    return data.model_copy(update={"connected_by_email": email})


def list_connected_accounts(session: Session, company_id: int) -> list[ConnectedAccountRead]:
    accounts = session.exec(
        select(ConnectedAccount)
        .where(ConnectedAccount.company_id == company_id)
        .order_by(ConnectedAccount.platform, ConnectedAccount.is_mock, ConnectedAccount.account_name)
    ).all()
    return [connected_account_to_read(session, a) for a in accounts]


def list_queued_items(session: Session, company_id: int) -> list[QueueItemRead]:
    rows = session.exec(
        select(ContentCalendarItem, GeneratedPost)
        .join(GeneratedPost, GeneratedPost.id == ContentCalendarItem.generated_post_id)
        .where(
            ContentCalendarItem.company_id == company_id,
            ContentCalendarItem.status == CalendarItemStatus.queued,
        )
        .order_by(ContentCalendarItem.updated_at.desc())
    ).all()
    result: list[QueueItemRead] = []
    for item, post in rows:
        content = _parse_content(json.loads(post.content_json))
        result.append(
            QueueItemRead(
                id=item.id,
                company_id=item.company_id,
                platform=item.platform,
                status=item.status,
                hook_preview=item.hook_preview,
                scheduled_date=item.scheduled_date,
                scheduled_time=item.scheduled_time,
                image_file_id=post.image_file_id,
                content=content,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
        )
    return result


def list_publishing_jobs(session: Session, company_id: int, limit: int = 50) -> list[PublishingJobRead]:
    rows = session.exec(
        select(PublishingJob, ContentCalendarItem, GeneratedPost)
        .join(ContentCalendarItem, ContentCalendarItem.id == PublishingJob.calendar_item_id)
        .join(GeneratedPost, GeneratedPost.id == ContentCalendarItem.generated_post_id)
        .where(PublishingJob.company_id == company_id)
        .order_by(PublishingJob.created_at.desc())
        .limit(limit)
    ).all()
    return [_job_to_read(job, item, post) for job, item, post in rows]


def mock_publish(session: Session, company_id: int, item_id: int) -> PublishResponse:
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

    item, post = row
    if item.status != CalendarItemStatus.queued:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot publish while status is '{item.status.value}'",
        )

    account = _get_mock_account(session, company_id, item.platform)
    external_id = f"mock-{item.platform.value}-{uuid.uuid4().hex[:12]}"

    job = PublishingJob(
        company_id=company_id,
        calendar_item_id=item.id,
        connected_account_id=account.id,
        status=PublishingJobStatus.running,
        attempts=1,
    )
    session.add(job)
    session.flush()

    job.status = PublishingJobStatus.completed
    job.result_message = f"Mock published to {account.account_name}"
    job.external_post_id = external_id
    job.completed_at = datetime.utcnow()

    item.status = CalendarItemStatus.published
    item.updated_at = datetime.utcnow()

    session.add(job)
    session.add(item)
    session.commit()
    session.refresh(job)
    session.refresh(item)

    return PublishResponse(
        job=_job_to_read(job, item, post),
        calendar_item=_to_calendar_item_read(item, post),
    )


def mock_publish_all(session: Session, company_id: int) -> list[PublishResponse]:
    queued = list_queued_items(session, company_id)
    if not queued:
        return []
    results: list[PublishResponse] = []
    for entry in queued:
        results.append(mock_publish(session, company_id, entry.id))
    return results
