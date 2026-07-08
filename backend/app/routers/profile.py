from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.database import get_session
from app.models.profile import BrandProfile, CompanyProfile
from app.models.tenancy import Company, CompanyUser
from app.schemas.profile import (
    BrandProfileRead,
    BrandProfileUpdate,
    CompanyProfileRead,
    CompanyProfileUpdate,
)
from app.security import get_current_company, require_company_editor

router = APIRouter(prefix="/companies/{company_id}", tags=["profiles"])


def _empty_company_profile(company_id: int) -> CompanyProfileRead:
    return CompanyProfileRead(company_id=company_id)


def _empty_brand_profile(company_id: int) -> BrandProfileRead:
    return BrandProfileRead(company_id=company_id)


@router.get("/profile", response_model=CompanyProfileRead)
def get_company_profile(
    company: Annotated[Company, Depends(get_current_company)],
    session: Annotated[Session, Depends(get_session)],
) -> CompanyProfileRead:
    profile = session.exec(
        select(CompanyProfile).where(CompanyProfile.company_id == company.id)
    ).first()
    if profile is None:
        return _empty_company_profile(company.id)
    return CompanyProfileRead.model_validate(profile)


@router.put("/profile", response_model=CompanyProfileRead)
def upsert_company_profile(
    payload: CompanyProfileUpdate,
    company: Annotated[Company, Depends(get_current_company)],
    _: Annotated[CompanyUser, Depends(require_company_editor)],
    session: Annotated[Session, Depends(get_session)],
) -> CompanyProfileRead:
    profile = session.exec(
        select(CompanyProfile).where(CompanyProfile.company_id == company.id)
    ).first()

    data = payload.model_dump(exclude_unset=True)
    if profile is None:
        profile = CompanyProfile(company_id=company.id, **data)
        session.add(profile)
    else:
        for key, value in data.items():
            setattr(profile, key, value)
        profile.updated_at = datetime.utcnow()
        session.add(profile)

    session.commit()
    session.refresh(profile)
    return CompanyProfileRead.model_validate(profile)


@router.get("/brand", response_model=BrandProfileRead)
def get_brand_profile(
    company: Annotated[Company, Depends(get_current_company)],
    session: Annotated[Session, Depends(get_session)],
) -> BrandProfileRead:
    profile = session.exec(
        select(BrandProfile).where(BrandProfile.company_id == company.id)
    ).first()
    if profile is None:
        return _empty_brand_profile(company.id)
    return BrandProfileRead.model_validate(profile)


@router.put("/brand", response_model=BrandProfileRead)
def upsert_brand_profile(
    payload: BrandProfileUpdate,
    company: Annotated[Company, Depends(get_current_company)],
    _: Annotated[CompanyUser, Depends(require_company_editor)],
    session: Annotated[Session, Depends(get_session)],
) -> BrandProfileRead:
    profile = session.exec(
        select(BrandProfile).where(BrandProfile.company_id == company.id)
    ).first()

    data = payload.model_dump(exclude_unset=True)
    if profile is None:
        profile = BrandProfile(company_id=company.id, **data)
        session.add(profile)
    else:
        for key, value in data.items():
            setattr(profile, key, value)
        profile.updated_at = datetime.utcnow()
        session.add(profile)

    session.commit()
    session.refresh(profile)
    return BrandProfileRead.model_validate(profile)
