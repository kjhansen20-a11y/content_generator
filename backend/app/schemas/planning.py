from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.models.content import Platform, PostType
from app.models.planning import MarketingPlanStatus, PostingFrequency


class MarketingPlanRead(BaseModel):
    id: int
    company_id: int
    name: str
    period_start: date | None
    period_end: date | None
    status: MarketingPlanStatus
    goals: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MarketingPlanCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    period_start: date | None = None
    period_end: date | None = None
    goals: str | None = None
    notes: str | None = None


class MarketingPlanUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    period_start: date | None = None
    period_end: date | None = None
    status: MarketingPlanStatus | None = None
    goals: str | None = None
    notes: str | None = None


class ContentPillarRead(BaseModel):
    id: int
    company_id: int
    marketing_plan_id: int | None
    name: str
    description: str | None
    weight: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContentPillarCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    weight: int = Field(default=5, ge=1, le=10)
    marketing_plan_id: int | None = None


class ContentPillarUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    weight: int | None = Field(default=None, ge=1, le=10)
    marketing_plan_id: int | None = None


class PostingRuleRead(BaseModel):
    id: int
    company_id: int
    platform: Platform
    weekday: int
    post_time: str
    post_type: PostType
    frequency: PostingFrequency
    is_active: bool
    content_pillar_id: int | None = None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PostingRuleCreate(BaseModel):
    platform: Platform
    weekday: int = Field(ge=0, le=6)
    post_time: str = Field(default="09:00", max_length=8)
    post_type: PostType = PostType.professional
    frequency: PostingFrequency = PostingFrequency.weekly
    is_active: bool = True
    content_pillar_id: int | None = None
    notes: str | None = Field(default=None, max_length=500)


class PostingRuleUpdate(BaseModel):
    platform: Platform | None = None
    weekday: int | None = Field(default=None, ge=0, le=6)
    post_time: str | None = Field(default=None, max_length=8)
    post_type: PostType | None = None
    frequency: PostingFrequency | None = None
    is_active: bool | None = None
    content_pillar_id: int | None = None
    notes: str | None = Field(default=None, max_length=500)


class GenerateMarketingPlanRequest(BaseModel):
    keywords: str = Field(default="", max_length=2000)
    plan_expectations: str | None = Field(default=None, max_length=4000)
    focus_areas: str | None = Field(default=None, max_length=2000)
    platforms: list[Platform] = Field(default_factory=lambda: [Platform.linkedin])
    plan_name: str | None = Field(default=None, max_length=255)
    period_weeks: int | None = Field(default=12, ge=1, le=52)
    posts_per_week: int = Field(default=3, ge=1, le=21)
    replace_existing: bool = True

    @model_validator(mode="after")
    def keywords_or_expectations(self) -> "GenerateMarketingPlanRequest":
        if not self.keywords.strip() and not (self.plan_expectations or "").strip():
            raise ValueError("Provide keywords/themes or plan expectations & direction.")
        return self


class GenerateMarketingPlanResponse(BaseModel):
    plan: MarketingPlanRead
    pillars: list[ContentPillarRead]
    posting_rules: list[PostingRuleRead]
