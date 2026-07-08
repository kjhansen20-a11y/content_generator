from datetime import date, datetime

from pydantic import BaseModel

from app.models.content import CalendarItemStatus, Platform, PostType
from app.models.publishing import AccountStatus, PublishingJobStatus
from app.schemas.content import CalendarItemRead, GeneratedPostContent


class ConnectedAccountRead(BaseModel):
    id: int
    company_id: int
    platform: Platform
    account_name: str
    is_mock: bool
    status: AccountStatus
    external_account_id: str | None = None
    account_type: str | None = None
    token_expires_at: datetime | None = None
    scopes: str | None = None
    connected_by_user_id: int | None = None
    connected_by_email: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class PublishingJobRead(BaseModel):
    id: int
    company_id: int
    calendar_item_id: int
    connected_account_id: int
    status: PublishingJobStatus
    attempts: int
    result_message: str | None
    error_message: str | None
    external_post_id: str | None
    created_at: datetime
    completed_at: datetime | None
    hook_preview: str | None = None
    platform: Platform | None = None
    image_file_id: int | None = None
    content: GeneratedPostContent | None = None

    model_config = {"from_attributes": True}


class PublishResponse(BaseModel):
    job: PublishingJobRead
    calendar_item: CalendarItemRead


class QueueItemRead(BaseModel):
    id: int
    company_id: int
    platform: Platform
    post_type: PostType
    status: CalendarItemStatus
    hook_preview: str | None
    scheduled_date: date | None
    scheduled_time: str | None = None
    image_file_id: int | None = None
    content: GeneratedPostContent
    created_at: datetime
    updated_at: datetime
