from datetime import datetime

from pydantic import BaseModel, Field

from app.models.knowledge import FileKind


class KnowledgeCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1, max_length=50000)


class KnowledgeRead(BaseModel):
    id: int
    company_id: int
    title: str
    content: str
    source: str
    uploaded_file_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UploadedFileRead(BaseModel):
    id: int
    company_id: int
    original_filename: str
    mime_type: str
    size_bytes: int
    kind: FileKind
    created_at: datetime

    model_config = {"from_attributes": True}
