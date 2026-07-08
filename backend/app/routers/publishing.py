from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.database import get_session
from app.models.auth import User
from app.models.tenancy import Company, CompanyUser
from app.schemas.publishing import (
    ConnectedAccountRead,
    PublishResponse,
    PublishingJobRead,
    QueueItemRead,
)
from app.security import get_current_user, get_current_company, require_company_editor
from app.services.publishing import (
    list_connected_accounts,
    list_publishing_jobs,
    list_queued_items,
    publish_all,
    publish_item,
)

router = APIRouter(prefix="/companies/{company_id}", tags=["publishing"])


@router.get("/connected-accounts", response_model=list[ConnectedAccountRead])
def get_connected_accounts(
    company: Annotated[Company, Depends(get_current_company)],
    session: Annotated[Session, Depends(get_session)],
) -> list[ConnectedAccountRead]:
    return list_connected_accounts(session, company.id)


@router.get("/publishing/queue", response_model=list[QueueItemRead])
def get_publishing_queue(
    company: Annotated[Company, Depends(get_current_company)],
    session: Annotated[Session, Depends(get_session)],
) -> list[QueueItemRead]:
    return list_queued_items(session, company.id)


@router.get("/publishing/jobs", response_model=list[PublishingJobRead])
def get_publishing_jobs(
    company: Annotated[Company, Depends(get_current_company)],
    session: Annotated[Session, Depends(get_session)],
) -> list[PublishingJobRead]:
    return list_publishing_jobs(session, company.id)


@router.post("/calendar/{item_id}/publish", response_model=PublishResponse)
def publish_calendar_item(
    item_id: int,
    company: Annotated[Company, Depends(get_current_company)],
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[CompanyUser, Depends(require_company_editor)],
    session: Annotated[Session, Depends(get_session)],
) -> PublishResponse:
    return publish_item(session, company.id, item_id, user_id=current_user.id)


@router.post("/publishing/publish-all", response_model=list[PublishResponse])
def publish_all_queued(
    company: Annotated[Company, Depends(get_current_company)],
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[CompanyUser, Depends(require_company_editor)],
    session: Annotated[Session, Depends(get_session)],
) -> list[PublishResponse]:
    return publish_all(session, company.id, user_id=current_user.id)
