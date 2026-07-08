from pydantic import BaseModel, Field

from app.models.content import Platform


class OAuthStartRequest(BaseModel):
    connection_kind: str = Field(
        default="profile",
        description="profile = user's own LinkedIn identity; page = Facebook Page",
    )


class OAuthStartResponse(BaseModel):
    authorization_url: str
    platform: Platform
    connection_kind: str


class OAuthStatusResponse(BaseModel):
    linkedin_configured: bool
    facebook_configured: bool
    linkedin_redirect_uri: str
    linkedin_scopes: str
    privacy_policy_url: str


class FacebookPageOption(BaseModel):
    id: str
    name: str


class CompleteFacebookPageRequest(BaseModel):
    pending_id: str
    page_id: str
