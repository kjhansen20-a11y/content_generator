from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse, Response
from sqlmodel import Session

from app.database import get_session
from app.models.knowledge import FileKind
from app.models.tenancy import Company, CompanyUser
from app.schemas.knowledge import KnowledgeCreate, KnowledgeRead, UploadedFileRead
from app.security import get_current_company, require_company_editor
from app.services.files import (
    create_knowledge_from_upload,
    file_path,
    get_uploaded_file,
    read_file_bytes,
    save_upload,
)
from app.services.knowledge import create_knowledge, delete_knowledge, list_knowledge

router = APIRouter(prefix="/companies/{company_id}", tags=["knowledge"])


@router.get("/knowledge", response_model=list[KnowledgeRead])
def get_knowledge(
    company: Annotated[Company, Depends(get_current_company)],
    session: Annotated[Session, Depends(get_session)],
) -> list[KnowledgeRead]:
    return list_knowledge(session, company.id)


@router.post("/knowledge", response_model=KnowledgeRead)
def add_knowledge(
    payload: KnowledgeCreate,
    company: Annotated[Company, Depends(get_current_company)],
    _: Annotated[CompanyUser, Depends(require_company_editor)],
    session: Annotated[Session, Depends(get_session)],
) -> KnowledgeRead:
    return create_knowledge(session, company.id, payload)


@router.delete("/knowledge/{entry_id}", status_code=204)
def remove_knowledge(
    entry_id: int,
    company: Annotated[Company, Depends(get_current_company)],
    _: Annotated[CompanyUser, Depends(require_company_editor)],
    session: Annotated[Session, Depends(get_session)],
) -> None:
    delete_knowledge(session, company.id, entry_id)


@router.post("/files", response_model=UploadedFileRead)
async def upload_file(
    company: Annotated[Company, Depends(get_current_company)],
    _: Annotated[CompanyUser, Depends(require_company_editor)],
    session: Annotated[Session, Depends(get_session)],
    file: UploadFile = File(...),
    kind: FileKind = Query(default=FileKind.knowledge),
    knowledge_source: str = Query(default="upload", max_length=128),
) -> UploadedFileRead:
    record = await save_upload(session, company.id, file, kind)
    if kind == FileKind.knowledge:
        create_knowledge_from_upload(session, record, source=knowledge_source)
    return UploadedFileRead.model_validate(record)


@router.get("/files/{file_id}")
def download_file(
    file_id: int,
    company: Annotated[Company, Depends(get_current_company)],
    session: Annotated[Session, Depends(get_session)],
) -> FileResponse:
    record = get_uploaded_file(session, company.id, file_id)
    path = file_path(record)
    if path.exists():
        return FileResponse(path, media_type=record.mime_type, filename=record.original_filename)
    data = read_file_bytes(record)
    return Response(content=data, media_type=record.mime_type)
