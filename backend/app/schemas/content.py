from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.models.content import (
    CalendarItemStatus,
    CREATABLE_PLATFORMS,
    GenerateMode,
    Platform,
    PostType,
)


class GeneratedPostContent(BaseModel):
    hook: str
    body: str
    hashtags: list[str] = Field(default_factory=list)
    platform: str
    post_type: str
    alt_text: str | None = None
    quality_notes: str | None = None
    compliance_notes: str | None = None
    suggested_publish_time: str | None = None


class GeneratePostRequest(BaseModel):
    mode: GenerateMode = GenerateMode.instant
    post_type: PostType | None = None
    platform: Platform | None = None
    content_idea: str | None = Field(default=None, max_length=4000)
    image_notes: str | None = Field(default=None, max_length=2000)
    image_file_id: int | None = None
    image_description: str | None = Field(default=None, max_length=2000)
    keywords: str | None = Field(default=None, max_length=1000)
    output_language: str = Field(default="auto", max_length=10)
    scheduled_date: date | None = None
    scheduled_time: str | None = Field(default=None, max_length=5)
    use_next_week: bool = False

    @model_validator(mode="after")
    def validate_mode_fields(self) -> "GeneratePostRequest":
        if self.mode == GenerateMode.instant:
            if self.post_type is None or self.platform is None:
                raise ValueError("post_type and platform are required for instant posts")
            if self.platform not in CREATABLE_PLATFORMS:
                raise ValueError("platform must be linkedin or facebook")
        if self.mode == GenerateMode.scheduled_manual:
            if self.post_type is None or self.platform is None:
                raise ValueError("post_type and platform are required for manual scheduling")
            if self.platform not in CREATABLE_PLATFORMS:
                raise ValueError("platform must be linkedin or facebook")
            if self.scheduled_date is None:
                raise ValueError("scheduled_date is required for manual scheduling")
        return self


class GeneratedPostRead(BaseModel):
    id: int
    company_id: int
    platform: Platform
    post_type: PostType
    content: GeneratedPostContent
    model: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CalendarItemRead(BaseModel):
    id: int
    company_id: int
    generated_post_id: int
    scheduled_date: date | None
    scheduled_time: str | None = None
    posting_rule_id: int | None = None
    content_pillar_id: int | None = None
    platform: Platform
    post_type: PostType
    status: CalendarItemStatus
    hook_preview: str | None
    image_file_id: int | None = None
    content: GeneratedPostContent
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GeneratePostResponse(BaseModel):
    generated_post: GeneratedPostRead
    calendar_item: CalendarItemRead
    slot_label: str | None = None


class CalendarItemContentUpdate(BaseModel):
    hook: str = Field(min_length=1, max_length=2000)
    body: str = Field(min_length=1, max_length=10000)
    hashtags: list[str] = Field(default_factory=list)
    alt_text: str | None = Field(default=None, max_length=2000)
    suggested_publish_time: str | None = Field(default=None, max_length=255)
    scheduled_date: date | None = None
    scheduled_time: str | None = Field(default=None, max_length=5)


class WeekSlotRead(BaseModel):
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


class WeekSlotsResponse(BaseModel):
    week_start: date
    week_end: date
    slots: list[WeekSlotRead]
    all_filled: bool

