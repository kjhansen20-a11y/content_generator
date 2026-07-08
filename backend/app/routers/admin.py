from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.database import get_session
from app.models.auth import User
from app.schemas.admin import (
    AdminCompanyRead,
    AdminJobRead,
    AdminPromptRead,
    AdminUsageSummary,
    AdminUserRead,
)
from app.security import require_platform_admin
from app.services.admin import (
    get_usage_summary,
    list_admin_companies,
    list_admin_jobs,
    list_admin_prompts,
    list_admin_users,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/companies", response_model=list[AdminCompanyRead])
def admin_companies(
    _: Annotated[User, Depends(require_platform_admin)],
    session: Annotated[Session, Depends(get_session)],
) -> list[AdminCompanyRead]:
    return list_admin_companies(session)


@router.get("/usage", response_model=AdminUsageSummary)
def admin_usage(
    _: Annotated[User, Depends(require_platform_admin)],
    session: Annotated[Session, Depends(get_session)],
) -> AdminUsageSummary:
    return get_usage_summary(session)


@router.get("/users", response_model=list[AdminUserRead])
def admin_users(
    _: Annotated[User, Depends(require_platform_admin)],
    session: Annotated[Session, Depends(get_session)],
) -> list[AdminUserRead]:
    return list_admin_users(session)


@router.get("/prompts", response_model=list[AdminPromptRead])
def admin_prompts(
    _: Annotated[User, Depends(require_platform_admin)],
    session: Annotated[Session, Depends(get_session)],
) -> list[AdminPromptRead]:
    return list_admin_prompts(session)


@router.get("/jobs", response_model=list[AdminJobRead])
def admin_jobs(
    _: Annotated[User, Depends(require_platform_admin)],
    session: Annotated[Session, Depends(get_session)],
) -> list[AdminJobRead]:
    return list_admin_jobs(session)
