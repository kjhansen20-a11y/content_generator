import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlmodel import Session, select

from app.config import BACKEND_DIR, get_settings
from app.models.knowledge import CompanyKnowledge, FileKind, UploadedFile
from app.services.text_extract import extract_text_from_bytes

settings = get_settings()

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_KNOWLEDGE_TYPES = {
    "text/plain",
    "text/markdown",
    "text/csv",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def uploads_root() -> Path:
    path = BACKEND_DIR / settings.uploads_dir
    path.mkdir(parents=True, exist_ok=True)
    return path


def company_upload_dir(company_id: int) -> Path:
    path = uploads_root() / str(company_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _safe_filename(name: str) -> str:
    return Path(name).name.replace("..", "").strip() or "file"


async def save_upload(
    session: Session,
    company_id: int,
    upload: UploadFile,
    kind: FileKind,
) -> UploadedFile:
    if upload.filename is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required")

    content_type = upload.content_type or "application/octet-stream"
    if kind == FileKind.post_image and content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image must be JPEG, PNG, WebP, or GIF",
        )
    if kind == FileKind.knowledge and content_type not in ALLOWED_KNOWLEDGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported document type for knowledge upload",
        )

    data = await upload.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large (max {settings.max_upload_mb} MB)",
        )

    original = _safe_filename(upload.filename)
    stored = f"{uuid.uuid4().hex}_{original}"
    dest = company_upload_dir(company_id) / stored
    dest.write_bytes(data)

    record = UploadedFile(
        company_id=company_id,
        original_filename=original,
        stored_filename=stored,
        mime_type=content_type,
        size_bytes=len(data),
        kind=kind,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def get_uploaded_file(session: Session, company_id: int, file_id: int) -> UploadedFile:
    record = session.get(UploadedFile, file_id)
    if record is None or record.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return record


def file_path(record: UploadedFile) -> Path:
    return company_upload_dir(record.company_id) / record.stored_filename


def extract_text_from_file(record: UploadedFile) -> str | None:
    path = file_path(record)
    if not path.exists():
        return None
    try:
        return extract_text_from_bytes(
            record.original_filename,
            path.read_bytes(),
            record.mime_type,
        )
    except ValueError:
        return None


def create_knowledge_from_upload(
    session: Session,
    record: UploadedFile,
    *,
    source: str = "upload",
) -> CompanyKnowledge | None:
    extracted = extract_text_from_file(record)
    if not extracted:
        return None
    entry = CompanyKnowledge(
        company_id=record.company_id,
        title=record.original_filename,
        content=extracted,
        source=source,
        uploaded_file_id=record.id,
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry
