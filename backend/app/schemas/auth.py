from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    company_name: str = Field(min_length=1, max_length=255)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    id: int
    email: EmailStr
    is_platform_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CompanyRead(BaseModel):
    id: int
    name: str
    slug: str
    role: str

    model_config = {"from_attributes": True}


class MeResponse(BaseModel):
    user: UserRead
    companies: list[CompanyRead]
