from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx

from app.config import get_settings

LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
LINKEDIN_ORG_ACLS_URL = "https://api.linkedin.com/v2/organizationAcls"
LINKEDIN_ORG_URL = "https://api.linkedin.com/v2/organizations"

# Personal posts: w_member_social (Share on LinkedIn).
# Company page posts: org scopes (Community Management API product).
LINKEDIN_SCOPES_BASE = [
    "openid",
    "profile",
    "email",
    "w_member_social",
]
LINKEDIN_SCOPES_ORG = [
    "r_organization_admin",
    "w_organization_social",
]


def linkedin_scopes() -> list[str]:
    settings = get_settings()
    scopes = list(LINKEDIN_SCOPES_BASE)
    if settings.linkedin_include_org_scopes:
        scopes.extend(LINKEDIN_SCOPES_ORG)
    return scopes


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


@dataclass
class LinkedInOrganization:
    external_id: str
    display_name: str


def _linkedin_headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0",
    }


def _organization_name(client: httpx.Client, access_token: str, org_id: str) -> str:
    response = client.get(
        f"{LINKEDIN_ORG_URL}/{org_id}",
        params={"projection": "(localizedName)"},
        headers=_linkedin_headers(access_token),
    )
    if response.is_error:
        return f"Company Page {org_id}"
    localized = response.json().get("localizedName")
    if isinstance(localized, dict):
        return str(localized.get("en_US") or next(iter(localized.values()), f"Company Page {org_id}"))
    if isinstance(localized, str) and localized.strip():
        return localized
    return f"Company Page {org_id}"


def linkedin_list_admin_organizations(access_token: str) -> list[LinkedInOrganization]:
    """Return LinkedIn Company Pages the member can administer."""
    organizations: list[LinkedInOrganization] = []
    seen: set[str] = set()

    with httpx.Client(timeout=30) as client:
        response = client.get(
            LINKEDIN_ORG_ACLS_URL,
            params={"q": "roleAssignee", "role": "ADMINISTRATOR"},
            headers=_linkedin_headers(access_token),
        )
        if response.status_code in (403, 401):
            return []
        response.raise_for_status()
        elements = response.json().get("elements") or []

        for element in elements:
            org_ref = element.get("organization") or element.get("organizationalTarget") or ""
            org_id = str(org_ref).split(":")[-1]
            if not org_id or org_id in seen:
                continue
            seen.add(org_id)
            organizations.append(
                LinkedInOrganization(
                    external_id=org_id,
                    display_name=_organization_name(client, access_token, org_id),
                )
            )

    return organizations


def linkedin_authorization_url(state: str) -> str:
    settings = get_settings()
    params = {
        "response_type": "code",
        "client_id": settings.linkedin_client_id,
        "redirect_uri": settings.linkedin_redirect_uri,
        "state": state,
        "scope": " ".join(linkedin_scopes()),
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
        scopes=payload.get("scope", " ".join(linkedin_scopes())),
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
    return OAuthProfile(external_id=external_id, display_name=name, account_type="profile")
