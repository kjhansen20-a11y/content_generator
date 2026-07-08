from datetime import datetime

from pydantic import BaseModel, Field


class CompanyProfileRead(BaseModel):
    company_id: int
    legal_name: str | None = None
    description: str | None = None
    industry: str | None = None
    website: str | None = None
    location: str | None = None
    target_audience: str | None = None
    products_services: str | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class CompanyProfileUpdate(BaseModel):
    legal_name: str | None = Field(default=None, max_length=255)
    description: str | None = None
    industry: str | None = Field(default=None, max_length=255)
    website: str | None = Field(default=None, max_length=512)
    location: str | None = Field(default=None, max_length=255)
    target_audience: str | None = None
    products_services: str | None = None


class BrandProfileRead(BaseModel):
    company_id: int
    tone_of_voice: str | None = None
    brand_voice_description: str | None = None
    do_use: str | None = None
    dont_use: str | None = None
    brand_keywords: str | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class BrandProfileUpdate(BaseModel):
    tone_of_voice: str | None = Field(default=None, max_length=255)
    brand_voice_description: str | None = None
    do_use: str | None = None
    dont_use: str | None = None
    brand_keywords: str | None = None
