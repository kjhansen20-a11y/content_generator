from datetime import datetime

from pydantic import BaseModel


class AdminCompanyRead(BaseModel):
    id: int
    name: str
    slug: str
    member_count: int
    post_count: int
    total_tokens: int
    total_cost_usd: float
    created_at: datetime


class AdminUsageSummary(BaseModel):
    total_events: int
    total_tokens: int
    total_cost_usd: float
    by_company: list[AdminCompanyRead]


class AdminUserRead(BaseModel):
    id: int
    email: str
    is_platform_admin: bool
    company_count: int
    created_at: datetime


class AdminPromptRead(BaseModel):
    id: int
    key: str
    kind: str
    description: str | None
    active_version: int | None
    active_version_id: int | None
    body_preview: str | None


class AdminJobRead(BaseModel):
    id: int
    company_id: int
    company_name: str
    calendar_item_id: int
    status: str
    platform: str | None
    hook_preview: str | None
    external_post_id: str | None
    created_at: datetime
    completed_at: datetime | None
