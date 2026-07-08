from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class PromptTemplate(SQLModel, table=True):
    __tablename__ = "prompt_templates"

    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(unique=True, index=True, max_length=128)
    kind: str = Field(max_length=64)
    description: Optional[str] = Field(default=None, max_length=512)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PromptVersion(SQLModel, table=True):
    __tablename__ = "prompt_versions"

    id: Optional[int] = Field(default=None, primary_key=True)
    template_id: int = Field(foreign_key="prompt_templates.id", index=True)
    version: int = Field(default=1)
    body: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
