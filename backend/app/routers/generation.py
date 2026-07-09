from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.database import get_session
from app.models.tenancy import Company, CompanyUser
from app.schemas.content import CalendarItemRead, CalendarItemContentUpdate, GeneratePostRequest, GeneratePostResponse, WeekSlotsResponse
from app.security import get_current_company, require_company_editor
from app.services.calendar import approve_calendar_item, delete_calendar_item, queue_calendar_item, update_calendar_item
from app.services.generation import generate_post, get_week_slots, list_calendar_items

router = APIRouter(prefix="/companies/{company_id}", tags=["generation"])


@router.get("/planning/week-slots", response_model=WeekSlotsResponse)
def get_plan_week_slots(
    company: Annotated[Company, Depends(get_current_company)],
    session: Annotated[Session, Depends(get_session)],
    week: date | None = Query(default=None),
) -> WeekSlotsResponse:
    return get_week_slots(session, company.id, week)


@router.post("/generate", response_model=GeneratePostResponse)
def create_generated_post(
    payload: GeneratePostRequest,
    company: Annotated[Company, Depends(get_current_company)],
    _: Annotated[CompanyUser, Depends(require_company_editor)],
    session: Annotated[Session, Depends(get_session)],
) -> GeneratePostResponse:
    return generate_post(session, company, payload)


@router.get("/calendar", response_model=list[CalendarItemRead])
def get_calendar(
    company: Annotated[Company, Depends(get_current_company)],
    session: Annotated[Session, Depends(get_session)],
) -> list[CalendarItemRead]:
    return list_calendar_items(session, company.id)


@router.put("/calendar/{item_id}", response_model=CalendarItemRead)
def edit_calendar_item(
    item_id: int,
    payload: CalendarItemContentUpdate,
    company: Annotated[Company, Depends(get_current_company)],
    _: Annotated[CompanyUser, Depends(require_company_editor)],
    session: Annotated[Session, Depends(get_session)],
) -> CalendarItemRead:
    return update_calendar_item(session, company.id, item_id, payload)


@router.post("/calendar/{item_id}/approve", response_model=CalendarItemRead)
def approve_item(
    item_id: int,
    company: Annotated[Company, Depends(get_current_company)],
    _: Annotated[CompanyUser, Depends(require_company_editor)],
    session: Annotated[Session, Depends(get_session)],
) -> CalendarItemRead:
    return approve_calendar_item(session, company.id, item_id)


@router.post("/calendar/{item_id}/queue", response_model=CalendarItemRead)
def queue_item(
    item_id: int,
    company: Annotated[Company, Depends(get_current_company)],
    _: Annotated[CompanyUser, Depends(require_company_editor)],
    session: Annotated[Session, Depends(get_session)],
) -> CalendarItemRead:
    return queue_calendar_item(session, company.id, item_id)


@router.delete("/calendar/{item_id}", status_code=204)
def remove_calendar_item(
    item_id: int,
    company: Annotated[Company, Depends(get_current_company)],
    _: Annotated[CompanyUser, Depends(require_company_editor)],
    session: Annotated[Session, Depends(get_session)],
) -> None:
    delete_calendar_item(session, company.id, item_id)
