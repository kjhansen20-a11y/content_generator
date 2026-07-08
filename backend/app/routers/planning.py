from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlmodel import Session

from app.database import get_session
from app.models.tenancy import Company, CompanyUser
from app.schemas.content import WeekSlotsResponse
from app.schemas.planning import (
    ContentPillarCreate,
    ContentPillarRead,
    ContentPillarUpdate,
    GenerateMarketingPlanRequest,
    GenerateMarketingPlanResponse,
    MarketingPlanCreate,
    MarketingPlanRead,
    MarketingPlanUpdate,
    PostingRuleCreate,
    PostingRuleRead,
    PostingRuleUpdate,
)
from app.security import get_current_company, require_company_editor
from app.services.planning import (
    create_content_pillar,
    create_marketing_plan,
    create_posting_rule,
    delete_content_pillar,
    delete_marketing_plan,
    delete_posting_rule,
    generate_marketing_plan_with_ai,
    get_active_marketing_plan,
    import_marketing_plan_from_document,
    list_content_pillars,
    list_marketing_plans,
    list_posting_rules,
    update_content_pillar,
    update_marketing_plan,
    update_posting_rule,
)
from app.services.generation import get_week_slots

router = APIRouter(prefix="/companies/{company_id}", tags=["planning"])


@router.get("/marketing-plans/week-slots", response_model=WeekSlotsResponse)
def get_marketing_plan_week_slots(
    company: Annotated[Company, Depends(get_current_company)],
    session: Annotated[Session, Depends(get_session)],
    week: date | None = Query(default=None),
) -> WeekSlotsResponse:
    return get_week_slots(session, company.id, week)


@router.get("/marketing-plans", response_model=list[MarketingPlanRead])
def get_marketing_plans(
    company: Annotated[Company, Depends(get_current_company)],
    session: Annotated[Session, Depends(get_session)],
) -> list[MarketingPlanRead]:
    return list_marketing_plans(session, company.id)


@router.get("/marketing-plans/active", response_model=MarketingPlanRead | None)
def get_active_plan(
    company: Annotated[Company, Depends(get_current_company)],
    session: Annotated[Session, Depends(get_session)],
) -> MarketingPlanRead | None:
    plan = get_active_marketing_plan(session, company.id)
    return MarketingPlanRead.model_validate(plan) if plan else None


@router.post("/marketing-plans/generate", response_model=GenerateMarketingPlanResponse)
def generate_marketing_plan(
    payload: GenerateMarketingPlanRequest,
    company: Annotated[Company, Depends(get_current_company)],
    _: Annotated[CompanyUser, Depends(require_company_editor)],
    session: Annotated[Session, Depends(get_session)],
) -> GenerateMarketingPlanResponse:
    return generate_marketing_plan_with_ai(session, company, payload)


@router.post("/marketing-plans/import", response_model=GenerateMarketingPlanResponse)
async def import_marketing_plan(
    company: Annotated[Company, Depends(get_current_company)],
    _: Annotated[CompanyUser, Depends(require_company_editor)],
    session: Annotated[Session, Depends(get_session)],
    file: Annotated[UploadFile, File()],
    plan_name: Annotated[str | None, Form()] = None,
    replace_existing: Annotated[bool, Form()] = True,
) -> GenerateMarketingPlanResponse:
    if file.filename is None:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required")
    file_bytes = await file.read()
    return import_marketing_plan_from_document(
        session,
        company,
        filename=file.filename,
        file_bytes=file_bytes,
        mime_type=file.content_type,
        plan_name=plan_name.strip() if plan_name and plan_name.strip() else None,
        replace_existing=replace_existing,
    )


@router.post("/marketing-plans", response_model=MarketingPlanRead)
def add_marketing_plan(
    payload: MarketingPlanCreate,
    company: Annotated[Company, Depends(get_current_company)],
    _: Annotated[CompanyUser, Depends(require_company_editor)],
    session: Annotated[Session, Depends(get_session)],
) -> MarketingPlanRead:
    plan = create_marketing_plan(session, company.id, payload)
    return MarketingPlanRead.model_validate(plan)


@router.put("/marketing-plans/{plan_id}", response_model=MarketingPlanRead)
def edit_marketing_plan(
    plan_id: int,
    payload: MarketingPlanUpdate,
    company: Annotated[Company, Depends(get_current_company)],
    _: Annotated[CompanyUser, Depends(require_company_editor)],
    session: Annotated[Session, Depends(get_session)],
) -> MarketingPlanRead:
    plan = update_marketing_plan(session, company.id, plan_id, payload)
    return MarketingPlanRead.model_validate(plan)


@router.delete("/marketing-plans/{plan_id}", status_code=204)
def remove_marketing_plan(
    plan_id: int,
    company: Annotated[Company, Depends(get_current_company)],
    _: Annotated[CompanyUser, Depends(require_company_editor)],
    session: Annotated[Session, Depends(get_session)],
) -> None:
    delete_marketing_plan(session, company.id, plan_id)


@router.get("/content-pillars", response_model=list[ContentPillarRead])
def get_content_pillars(
    company: Annotated[Company, Depends(get_current_company)],
    session: Annotated[Session, Depends(get_session)],
) -> list[ContentPillarRead]:
    return list_content_pillars(session, company.id)


@router.post("/content-pillars", response_model=ContentPillarRead)
def add_content_pillar(
    payload: ContentPillarCreate,
    company: Annotated[Company, Depends(get_current_company)],
    _: Annotated[CompanyUser, Depends(require_company_editor)],
    session: Annotated[Session, Depends(get_session)],
) -> ContentPillarRead:
    pillar = create_content_pillar(session, company.id, payload)
    return ContentPillarRead.model_validate(pillar)


@router.put("/content-pillars/{pillar_id}", response_model=ContentPillarRead)
def edit_content_pillar(
    pillar_id: int,
    payload: ContentPillarUpdate,
    company: Annotated[Company, Depends(get_current_company)],
    _: Annotated[CompanyUser, Depends(require_company_editor)],
    session: Annotated[Session, Depends(get_session)],
) -> ContentPillarRead:
    pillar = update_content_pillar(session, company.id, pillar_id, payload)
    return ContentPillarRead.model_validate(pillar)


@router.delete("/content-pillars/{pillar_id}", status_code=204)
def remove_content_pillar(
    pillar_id: int,
    company: Annotated[Company, Depends(get_current_company)],
    _: Annotated[CompanyUser, Depends(require_company_editor)],
    session: Annotated[Session, Depends(get_session)],
) -> None:
    delete_content_pillar(session, company.id, pillar_id)


@router.get("/posting-rules", response_model=list[PostingRuleRead])
def get_posting_rules(
    company: Annotated[Company, Depends(get_current_company)],
    session: Annotated[Session, Depends(get_session)],
) -> list[PostingRuleRead]:
    return list_posting_rules(session, company.id)


@router.post("/posting-rules", response_model=PostingRuleRead)
def add_posting_rule(
    payload: PostingRuleCreate,
    company: Annotated[Company, Depends(get_current_company)],
    _: Annotated[CompanyUser, Depends(require_company_editor)],
    session: Annotated[Session, Depends(get_session)],
) -> PostingRuleRead:
    rule = create_posting_rule(session, company.id, payload)
    return PostingRuleRead.model_validate(rule)


@router.put("/posting-rules/{rule_id}", response_model=PostingRuleRead)
def edit_posting_rule(
    rule_id: int,
    payload: PostingRuleUpdate,
    company: Annotated[Company, Depends(get_current_company)],
    _: Annotated[CompanyUser, Depends(require_company_editor)],
    session: Annotated[Session, Depends(get_session)],
) -> PostingRuleRead:
    rule = update_posting_rule(session, company.id, rule_id, payload)
    return PostingRuleRead.model_validate(rule)


@router.delete("/posting-rules/{rule_id}", status_code=204)
def remove_posting_rule(
    rule_id: int,
    company: Annotated[Company, Depends(get_current_company)],
    _: Annotated[CompanyUser, Depends(require_company_editor)],
    session: Annotated[Session, Depends(get_session)],
) -> None:
    delete_posting_rule(session, company.id, rule_id)
