from datetime import date, datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class PostType(str, Enum):
    professional = "professional"
    personal = "personal"


class Platform(str, Enum):
    linkedin = "linkedin"
    facebook = "facebook"
    instagram = "instagram"


# Platforms users can pick when creating a post (drives publish routing).
CREATABLE_PLATFORMS = frozenset({Platform.linkedin, Platform.facebook})
PUBLISHABLE_PLATFORMS = frozenset({Platform.linkedin, Platform.facebook})


class GenerateMode(str, Enum):
    instant = "instant"
    scheduled_manual = "scheduled_manual"
    scheduled_follow_plan = "scheduled_follow_plan"


class CalendarItemStatus(str, Enum):
    draft = "draft"
    approved = "approved"
    queued = "queued"
    published = "published"
    failed = "failed"


FILLED_SLOT_STATUSES = {
    CalendarItemStatus.draft,
    CalendarItemStatus.approved,
    CalendarItemStatus.queued,
    CalendarItemStatus.published,
}


class GeneratedPost(SQLModel, table=True):
    __tablename__ = "generated_posts"

    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", index=True)
    platform: Platform
    post_type: PostType
    content_json: str
    model: str = Field(max_length=128)
    prompt_version_id: Optional[int] = Field(default=None, foreign_key="prompt_versions.id")
    image_file_id: Optional[int] = Field(default=None, foreign_key="uploaded_files.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ContentCalendarItem(SQLModel, table=True):
    __tablename__ = "content_calendar_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", index=True)
    generated_post_id: int = Field(foreign_key="generated_posts.id", index=True)
    scheduled_date: Optional[date] = Field(default=None, index=True)
    scheduled_time: Optional[str] = Field(default=None, max_length=5)
    posting_rule_id: Optional[int] = Field(default=None, foreign_key="posting_rules.id")
    content_pillar_id: Optional[int] = Field(default=None, foreign_key="content_pillars.id")
    platform: Platform
    post_type: PostType
    status: CalendarItemStatus = Field(default=CalendarItemStatus.draft)
    hook_preview: Optional[str] = Field(default=None, max_length=512)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PostVersion(SQLModel, table=True):
    __tablename__ = "post_versions"

    id: Optional[int] = Field(default=None, primary_key=True)
    generated_post_id: int = Field(foreign_key="generated_posts.id", index=True)
    content_json: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
