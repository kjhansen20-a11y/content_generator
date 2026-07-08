from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class CompanyProfile(SQLModel, table=True):
    __tablename__ = "company_profiles"

    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", unique=True, index=True)
    legal_name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None)
    industry: Optional[str] = Field(default=None, max_length=255)
    website: Optional[str] = Field(default=None, max_length=512)
    location: Optional[str] = Field(default=None, max_length=255)
    target_audience: Optional[str] = Field(default=None)
    products_services: Optional[str] = Field(default=None)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class BrandProfile(SQLModel, table=True):
    __tablename__ = "brand_profiles"

    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companies.id", unique=True, index=True)
    tone_of_voice: Optional[str] = Field(default=None, max_length=255)
    brand_voice_description: Optional[str] = Field(default=None)
    do_use: Optional[str] = Field(default=None)
    dont_use: Optional[str] = Field(default=None)
    brand_keywords: Optional[str] = Field(default=None)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
