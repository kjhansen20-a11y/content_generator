from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.database import get_session
from app.models.auth import User
from app.models.tenancy import Company, CompanyUser, CompanyUserRole
from app.schemas.auth import CompanyRead, MeResponse, TokenResponse, UserLogin, UserRead, UserRegister
from app.security import (
    create_access_token,
    get_current_user,
    get_user_by_email,
    get_user_companies,
    hash_password,
    unique_company_slug,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, session: Annotated[Session, Depends(get_session)]) -> TokenResponse:
    email = payload.email.lower()
    if get_user_by_email(session, email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(email=email, hashed_password=hash_password(payload.password))
    session.add(user)
    session.flush()

    company = Company(name=payload.company_name.strip(), slug=unique_company_slug(session, payload.company_name))
    session.add(company)
    session.flush()

    membership = CompanyUser(
        user_id=user.id,
        company_id=company.id,
        role=CompanyUserRole.owner,
    )
    session.add(membership)
    session.commit()

    return TokenResponse(access_token=create_access_token(user.email))


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, session: Annotated[Session, Depends(get_session)]) -> TokenResponse:
    user = get_user_by_email(session, payload.email.lower())
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    return TokenResponse(access_token=create_access_token(user.email))


@router.get("/me", response_model=MeResponse)
def me(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> MeResponse:
    companies = [
        CompanyRead(
            id=company.id,
            name=company.name,
            slug=company.slug,
            role=role.value,
        )
        for company, role in get_user_companies(session, current_user.id)
    ]
    return MeResponse(user=UserRead.model_validate(current_user), companies=companies)
