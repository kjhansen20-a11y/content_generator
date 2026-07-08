from datetime import date, datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel

from app.models.content import Platform, PostType


class MarketingPlanStatus(str, Enum):
    draft = "draft"
    active = "active"
    archived = "archived"


class PostingFrequency(str, Enum):
    daily = "daily"
    weekly = "weekly"
    biweekly = "biweekly"
    monthly = "monthly"


class MarketingPlan(SQLModel, table=True):
    __tablename__ = "marketing_plans"

    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", index=True)
    name: str = Field(max_length=255)
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    status: MarketingPlanStatus = Field(default=MarketingPlanStatus.draft)
    goals: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ContentPillar(SQLModel, table=True):
    __tablename__ = "content_pillars"

    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", index=True)
    marketing_plan_id: Optional[int] = Field(default=None, foreign_key="marketing_plans.id")
    name: str = Field(max_length=255)
    description: Optional[str] = None
    weight: int = Field(default=5, ge=1, le=10)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PostingRule(SQLModel, table=True):
    __tablename__ = "posting_rules"

    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", index=True)
    platform: Platform
    weekday: int = Field(ge=0, le=6, description="0=Monday, 6=Sunday")
    post_time: str = Field(max_length=8, default="09:00")
    post_type: PostType = Field(default=PostType.professional)
    frequency: PostingFrequency = Field(default=PostingFrequency.weekly)
    is_active: bool = Field(default=True)
    content_pillar_id: Optional[int] = Field(default=None, foreign_key="content_pillars.id")
    notes: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
