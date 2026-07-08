from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class FileKind(str, Enum):
    knowledge = "knowledge"
    post_image = "post_image"


class CompanyKnowledge(SQLModel, table=True):
    __tablename__ = "company_knowledge"

    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", index=True)
    title: str = Field(max_length=255)
    content: str
    source: str = Field(default="manual", max_length=128)
    uploaded_file_id: Optional[int] = Field(default=None, foreign_key="uploaded_files.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UploadedFile(SQLModel, table=True):
    __tablename__ = "uploaded_files"

    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", index=True)
    original_filename: str = Field(max_length=512)
    stored_filename: str = Field(max_length=512)
    mime_type: str = Field(max_length=128)
    size_bytes: int = Field(default=0)
    kind: FileKind = Field(default=FileKind.knowledge)
    created_at: datetime = Field(default_factory=datetime.utcnow)
