from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx

from app.config import get_settings

FACEBOOK_AUTH_URL = "https://www.facebook.com/v21.0/dialog/oauth"
FACEBOOK_TOKEN_URL = "https://graph.facebook.com/v21.0/oauth/access_token"
FACEBOOK_GRAPH = "https://graph.facebook.com/v21.0"

FACEBOOK_SCOPES = [
    "pages_manage_posts",
    "pages_read_engagement",
    "pages_show_list",
    "business_management",
]


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
    page_access_token: str | None = None


def facebook_authorization_url(state: str) -> str:
    settings = get_settings()
    params = {
        "client_id": settings.facebook_app_id,
        "redirect_uri": settings.facebook_redirect_uri,
        "state": state,
        "scope": ",".join(FACEBOOK_SCOPES),
        "response_type": "code",
    }
    return f"{FACEBOOK_AUTH_URL}?{urlencode(params)}"


def facebook_exchange_code(code: str) -> OAuthTokens:
    settings = get_settings()
    params = {
        "client_id": settings.facebook_app_id,
        "client_secret": settings.facebook_app_secret,
        "redirect_uri": settings.facebook_redirect_uri,
        "code": code,
    }
    with httpx.Client(timeout=30) as client:
        response = client.get(FACEBOOK_TOKEN_URL, params=params)
        response.raise_for_status()
        payload = response.json()

    expires_at = None
    if payload.get("expires_in"):
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(payload["expires_in"]))

    return OAuthTokens(
        access_token=payload["access_token"],
        refresh_token=None,
        expires_at=expires_at,
        scopes=",".join(FACEBOOK_SCOPES),
    )


def facebook_list_pages(user_access_token: str) -> list[dict]:
    with httpx.Client(timeout=30) as client:
        response = client.get(
            f"{FACEBOOK_GRAPH}/me/accounts",
            params={"fields": "id,name,access_token", "access_token": user_access_token},
        )
        response.raise_for_status()
        data = response.json()

    pages = data.get("data") or []
    if not pages:
        raise ValueError(
            "No Facebook Pages found on this account. Log in with the Facebook profile that manages your Page."
        )
    return pages


def facebook_fetch_page_profile(user_access_token: str) -> OAuthProfile:
    """Use the first managed Facebook Page when only one exists."""
    page = facebook_list_pages(user_access_token)[0]
    return OAuthProfile(
        external_id=str(page["id"]),
        display_name=str(page.get("name") or "Facebook Page"),
        account_type="page",
        page_access_token=page.get("access_token"),
    )
