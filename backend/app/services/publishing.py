import json
import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models.auth import User

from app.models.content import (
    CalendarItemStatus,
    ContentCalendarItem,
    GeneratedPost,
    Platform,
    PostType,
    PUBLISHABLE_PLATFORMS,
)
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
from app.services.files import get_uploaded_file, read_file_bytes
from app.services.generation import _parse_content, _to_calendar_item_read
from app.services.oauth import facebook_publish, linkedin_publish
from app.services.social_oauth import get_active_real_account
from app.services.token_crypto import decrypt_token


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
                post_type=item.post_type,
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


def _platform_label(platform: Platform) -> str:
    return platform.value.title()


def _require_publish_account(
    session: Session,
    company_id: int,
    platform: Platform,
    *,
    user_id: int | None,
    post_type: PostType | None = None,
) -> ConnectedAccount:
    if platform not in PUBLISHABLE_PLATFORMS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{_platform_label(platform)} publishing is not supported yet.",
        )
    account = get_active_real_account(
        session,
        company_id,
        platform,
        user_id=user_id,
        post_type=post_type,
    )
    if account is None:
        if platform == Platform.linkedin and post_type == PostType.personal:
            detail = (
                "This is a personal post. Connect your LinkedIn profile in Connections before publishing."
            )
        elif platform == Platform.linkedin:
            detail = (
                "This is a professional post and needs a LinkedIn Company Page you admin. "
                "Reconnect LinkedIn in Connections. Your LinkedIn app also needs the "
                "Community Management API product approved."
            )
        else:
            detail = (
                f"This post is set for {_platform_label(platform)}. "
                f"Connect {_platform_label(platform)} in Connections before publishing."
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    return account


def _account_access_token(account: ConnectedAccount, *, platform: Platform) -> str:
    if not account.access_token_encrypted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Connected account has no access token. Reconnect in Connections.",
        )
    if account.token_expires_at and account.token_expires_at <= datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{_platform_label(platform)} access token expired. Reconnect your account in Connections.",
        )
    try:
        return decrypt_token(account.access_token_encrypted)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not read stored {_platform_label(platform)} token. Reconnect your account.",
        ) from exc


def _load_post_image(
    session: Session,
    company_id: int,
    post: GeneratedPost,
) -> tuple[bytes | None, str | None]:
    if not post.image_file_id:
        return None, None
    upload = get_uploaded_file(session, company_id, post.image_file_id)
    try:
        return read_file_bytes(upload), upload.mime_type
    except HTTPException:
        return None, None


def _publish_to_linkedin(
    session: Session,
    *,
    company_id: int,
    post: GeneratedPost,
    account: ConnectedAccount,
) -> tuple[str, str]:
    if not account.external_account_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LinkedIn account is missing a profile id. Reconnect in Connections.",
        )

    content = _parse_content(json.loads(post.content_json))
    access_token = _account_access_token(account, platform=Platform.linkedin)
    image_bytes, image_mime = _load_post_image(session, company_id, post)
    image_missing = bool(post.image_file_id and not image_bytes)

    try:
        external_id = linkedin_publish.publish_post(
            access_token=access_token,
            external_account_id=account.external_account_id,
            content=content,
            image_bytes=image_bytes,
            image_mime_type=image_mime,
            account_type=account.account_type or "profile",
        )
    except linkedin_publish.LinkedInPublishError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    message = f"Published to LinkedIn ({account.account_name})"
    if image_missing:
        message += " (text only — image file was missing on the server)"
    return external_id, message


def _publish_to_facebook(
    session: Session,
    *,
    company_id: int,
    post: GeneratedPost,
    account: ConnectedAccount,
) -> tuple[str, str]:
    if not account.external_account_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Facebook Page is missing an id. Reconnect in Connections.",
        )

    content = _parse_content(json.loads(post.content_json))
    page_token = _account_access_token(account, platform=Platform.facebook)
    image_bytes, image_mime = _load_post_image(session, company_id, post)
    image_missing = bool(post.image_file_id and not image_bytes)

    try:
        external_id = facebook_publish.publish_post(
            page_id=account.external_account_id,
            page_access_token=page_token,
            content=content,
            image_bytes=image_bytes,
            image_mime_type=image_mime,
        )
    except facebook_publish.FacebookPublishError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    message = f"Published to Facebook Page {account.account_name}"
    if image_missing:
        message += " (text only — image file was missing on the server)"
    return external_id, message


def _run_platform_publish(
    session: Session,
    *,
    company_id: int,
    item: ContentCalendarItem,
    post: GeneratedPost,
    account: ConnectedAccount,
) -> tuple[str, str]:
    if item.platform == Platform.linkedin:
        return _publish_to_linkedin(session, company_id=company_id, post=post, account=account)
    if item.platform == Platform.facebook:
        return _publish_to_facebook(session, company_id=company_id, post=post, account=account)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"{_platform_label(item.platform)} publishing is not supported yet.",
    )


def _complete_publish_job(
    session: Session,
    *,
    job: PublishingJob,
    item: ContentCalendarItem,
    post: GeneratedPost,
    account: ConnectedAccount,
    external_id: str,
    result_message: str,
) -> PublishResponse:
    job.connected_account_id = account.id
    job.status = PublishingJobStatus.completed
    job.result_message = result_message
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


def _fail_publish_job(session: Session, job: PublishingJob, message: str) -> None:
    job.status = PublishingJobStatus.failed
    job.error_message = message
    job.completed_at = datetime.utcnow()
    session.add(job)
    session.commit()


def publish_item(
    session: Session,
    company_id: int,
    item_id: int,
    *,
    user_id: int | None = None,
) -> PublishResponse:
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

    account = _require_publish_account(
        session,
        company_id,
        item.platform,
        user_id=user_id,
        post_type=item.post_type,
    )

    job = PublishingJob(
        company_id=company_id,
        calendar_item_id=item.id,
        connected_account_id=account.id,
        status=PublishingJobStatus.running,
        attempts=1,
    )
    session.add(job)
    session.flush()

    try:
        external_id, result_message = _run_platform_publish(
            session,
            company_id=company_id,
            item=item,
            post=post,
            account=account,
        )
    except HTTPException as exc:
        _fail_publish_job(session, job, str(exc.detail))
        raise
    except Exception as exc:
        _fail_publish_job(session, job, str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Publishing failed: {exc}",
        ) from exc

    return _complete_publish_job(
        session,
        job=job,
        item=item,
        post=post,
        account=account,
        external_id=external_id,
        result_message=result_message,
    )


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


def publish_all(session: Session, company_id: int, *, user_id: int | None = None) -> list[PublishResponse]:
    queued = list_queued_items(session, company_id)
    if not queued:
        return []
    results: list[PublishResponse] = []
    for entry in queued:
        results.append(publish_item(session, company_id, entry.id, user_id=user_id))
    return results


def mock_publish_all(session: Session, company_id: int) -> list[PublishResponse]:
    return publish_all(session, company_id)
