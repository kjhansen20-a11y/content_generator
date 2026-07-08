import re
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import Session, select

from app.config import get_settings
from app.database import get_session
from app.models.auth import User
from app.models.tenancy import Company, CompanyUser, CompanyUserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security_scheme = HTTPBearer(auto_error=False)
settings = get_settings()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "company"


def unique_company_slug(session: Session, name: str) -> str:
    base = slugify(name)
    slug = base
    counter = 1
    while session.exec(select(Company).where(Company.slug == slug)).first():
        counter += 1
        slug = f"{base}-{counter}"
    return slug


def get_user_by_email(session: Session, email: str) -> User | None:
    return session.exec(select(User).where(User.email == email.lower())).first()


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
    session: Annotated[Session, Depends(get_session)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        email: str | None = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    user = get_user_by_email(session, email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_current_company(
    company_id: int,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Company:
    membership = session.exec(
        select(CompanyUser).where(
            CompanyUser.user_id == current_user.id,
            CompanyUser.company_id == company_id,
        )
    ).first()
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this company")

    company = session.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return company


def require_platform_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if not current_user.is_platform_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform admin required")
    return current_user


def get_user_companies(session: Session, user_id: int) -> list[tuple[Company, CompanyUserRole]]:
    rows = session.exec(
        select(Company, CompanyUser)
        .join(CompanyUser, CompanyUser.company_id == Company.id)
        .where(CompanyUser.user_id == user_id)
    ).all()
    return [(company, membership.role) for company, membership in rows]


def get_company_membership(
    session: Session,
    user_id: int,
    company_id: int,
) -> CompanyUser | None:
    return session.exec(
        select(CompanyUser).where(
            CompanyUser.user_id == user_id,
            CompanyUser.company_id == company_id,
        )
    ).first()


def require_company_editor(
    company_id: int,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CompanyUser:
    membership = get_company_membership(session, current_user.id, company_id)
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this company")
    if membership.role == CompanyUserRole.viewer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Editor access required")
    return membership
