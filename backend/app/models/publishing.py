from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel

from app.models.content import Platform


class AccountStatus(str, Enum):
    active = "active"
    inactive = "inactive"


class PublishingJobStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class ConnectedAccount(SQLModel, table=True):
    __tablename__ = "connected_accounts"

    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", index=True)
    platform: Platform
    account_name: str = Field(max_length=255)
    is_mock: bool = Field(default=True)
    status: AccountStatus = Field(default=AccountStatus.active)
    external_account_id: Optional[str] = Field(default=None, max_length=255)
    account_type: Optional[str] = Field(default=None, max_length=32)  # user | page | organization
    access_token_encrypted: Optional[str] = Field(default=None)
    refresh_token_encrypted: Optional[str] = Field(default=None)
    token_expires_at: Optional[datetime] = Field(default=None)
    scopes: Optional[str] = Field(default=None, max_length=1000)
    connected_by_user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PublishingJob(SQLModel, table=True):
    __tablename__ = "publishing_jobs"

    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", index=True)
    calendar_item_id: int = Field(foreign_key="content_calendar_items.id", index=True)
    connected_account_id: int = Field(foreign_key="connected_accounts.id", index=True)
    status: PublishingJobStatus = Field(default=PublishingJobStatus.pending)
    attempts: int = Field(default=0)
    result_message: Optional[str] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    external_post_id: Optional[str] = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
