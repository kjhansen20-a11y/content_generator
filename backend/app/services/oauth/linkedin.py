from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx

from app.config import get_settings

LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_USERINFO_URL = "https://api.linkedin.com/v2/userinfo"

# Post as member; org posting needs Marketing Developer Platform approval.
LINKEDIN_SCOPES = ["openid", "profile", "email", "w_member_social"]


@dataclass
class OAuthTokens:
    access_token: str
    refresh_token: str | None
    expires_at: datetime | None
    scopes: str


@dataclass
class OAuthProfile:
    external_id: str
    display_name: str
    account_type: str


def linkedin_authorization_url(state: str) -> str:
    settings = get_settings()
    params = {
        "response_type": "code",
        "client_id": settings.linkedin_client_id,
        "redirect_uri": settings.linkedin_redirect_uri,
        "state": state,
        "scope": " ".join(LINKEDIN_SCOPES),
    }
    return f"{LINKEDIN_AUTH_URL}?{urlencode(params)}"


def linkedin_exchange_code(code: str) -> OAuthTokens:
    settings = get_settings()
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.linkedin_redirect_uri,
        "client_id": settings.linkedin_client_id,
        "client_secret": settings.linkedin_client_secret,
    }
    with httpx.Client(timeout=30) as client:
        response = client.post(LINKEDIN_TOKEN_URL, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        response.raise_for_status()
        payload = response.json()

    expires_at = None
    if payload.get("expires_in"):
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(payload["expires_in"]))

    return OAuthTokens(
        access_token=payload["access_token"],
        refresh_token=payload.get("refresh_token"),
        expires_at=expires_at,
        scopes=payload.get("scope", " ".join(LINKEDIN_SCOPES)),
    )


def linkedin_fetch_profile(access_token: str) -> OAuthProfile:
    with httpx.Client(timeout=30) as client:
        response = client.get(
            LINKEDIN_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        data = response.json()

    name = data.get("name") or data.get("given_name") or "LinkedIn account"
    external_id = str(data.get("sub", ""))
    return OAuthProfile(external_id=external_id, display_name=name, account_type="user")
