from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class UsageEvent(SQLModel, table=True):
    __tablename__ = "usage_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", index=True)
    operation: str = Field(max_length=128)
    model: str = Field(max_length=128)
    prompt_tokens: int = Field(default=0)
    completion_tokens: int = Field(default=0)
    total_tokens: int = Field(default=0)
    estimated_cost_usd: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
