from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlmodel import Session

from app.config import get_settings
from app.database import get_session
from app.models.auth import User
from app.models.content import Platform
from app.models.tenancy import Company, CompanyUser
from app.schemas.oauth import (
    CompleteFacebookPageRequest,
    FacebookPageOption,
    OAuthStartRequest,
    OAuthStartResponse,
    OAuthStatusResponse,
)
from app.schemas.publishing import ConnectedAccountRead
from app.security import get_current_company, get_current_user, require_company_editor
from app.services.publishing import connected_account_to_read
from app.services.social_oauth import (
    complete_facebook_page_connection,
    disconnect_account,
    get_pending_facebook_pages,
    oauth_handle_callback,
    oauth_start_url,
)

router = APIRouter(prefix="/api/v1", tags=["oauth"])


@router.get("/oauth/status", response_model=OAuthStatusResponse)
def oauth_status() -> OAuthStatusResponse:
    settings = get_settings()
    from app.services.oauth import linkedin as linkedin_oauth

    return OAuthStatusResponse(
        linkedin_configured=settings.linkedin_oauth_configured(),
        facebook_configured=settings.facebook_oauth_configured(),
        linkedin_redirect_uri=settings.linkedin_redirect_uri,
        linkedin_scopes=" ".join(linkedin_oauth.LINKEDIN_SCOPES),
        privacy_policy_url=settings.privacy_policy_url,
    )


@router.post("/companies/{company_id}/oauth/{platform}/start", response_model=OAuthStartResponse)
def start_oauth(
    platform: str,
    payload: OAuthStartRequest,
    company: Annotated[Company, Depends(get_current_company)],
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[CompanyUser, Depends(require_company_editor)],
) -> OAuthStartResponse:
    if platform not in (Platform.linkedin.value, Platform.facebook.value):
        raise HTTPException(status_code=400, detail="Platform must be linkedin or facebook")
    kind = payload.connection_kind
    if platform == Platform.facebook.value:
        kind = "page"
    url = oauth_start_url(
        company_id=company.id,
        user_id=current_user.id,
        platform=platform,
        connection_kind=kind,
    )
    return OAuthStartResponse(authorization_url=url, platform=Platform(platform), connection_kind=kind)


@router.get("/oauth/linkedin/callback")
def linkedin_callback(
    session: Annotated[Session, Depends(get_session)],
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    error_description: str | None = Query(default=None),
) -> RedirectResponse:
    return _oauth_callback_redirect(
        session,
        platform=Platform.linkedin.value,
        code=code,
        state=state,
        error=error,
        error_description=error_description,
    )


@router.get("/oauth/facebook/callback")
def facebook_callback(
    session: Annotated[Session, Depends(get_session)],
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    error_description: str | None = Query(default=None),
) -> RedirectResponse:
    return _oauth_callback_redirect(
        session,
        platform=Platform.facebook.value,
        code=code,
        state=state,
        error=error,
        error_description=error_description,
    )


def _oauth_callback_redirect(
    session: Session,
    *,
    platform: str,
    code: str | None,
    state: str | None,
    error: str | None,
    error_description: str | None,
) -> RedirectResponse:
    settings = get_settings()
    base = settings.dashboard_url.rstrip("/")
    try:
        result = oauth_handle_callback(
            session,
            platform=platform,
            code=code,
            state=state,
            error=error,
            error_description=error_description,
        )
        if result.pending_id:
            params = urlencode(
                {"oauth": "pick_page", "platform": platform, "pending_id": result.pending_id}
            )
        else:
            name = result.account.account_name if result.account else platform
            params = urlencode({"oauth": "success", "platform": platform, "account": name})
    except HTTPException as exc:
        params = urlencode({"oauth": "error", "platform": platform, "message": str(exc.detail)})
    return RedirectResponse(url=f"{base}/?{params}")


@router.get(
    "/companies/{company_id}/oauth/facebook/pending-pages",
    response_model=list[FacebookPageOption],
)
def list_facebook_pending_pages(
    pending_id: str,
    company: Annotated[Company, Depends(get_current_company)],
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[CompanyUser, Depends(require_company_editor)],
    session: Annotated[Session, Depends(get_session)],
) -> list[FacebookPageOption]:
    pages = get_pending_facebook_pages(
        session,
        company_id=company.id,
        user_id=current_user.id,
        pending_id=pending_id,
    )
    return [FacebookPageOption(id=p["id"], name=p["name"]) for p in pages]


@router.post(
    "/companies/{company_id}/oauth/facebook/complete",
    response_model=ConnectedAccountRead,
)
def complete_facebook_page(
    payload: CompleteFacebookPageRequest,
    company: Annotated[Company, Depends(get_current_company)],
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[CompanyUser, Depends(require_company_editor)],
    session: Annotated[Session, Depends(get_session)],
) -> ConnectedAccountRead:
    account = complete_facebook_page_connection(
        session,
        company_id=company.id,
        user_id=current_user.id,
        pending_id=payload.pending_id,
        page_id=payload.page_id,
    )
    return connected_account_to_read(session, account)


@router.delete("/companies/{company_id}/connected-accounts/{account_id}", status_code=204)
def disconnect_connected_account(
    account_id: int,
    company: Annotated[Company, Depends(get_current_company)],
    _: Annotated[CompanyUser, Depends(require_company_editor)],
    session: Annotated[Session, Depends(get_session)],
) -> None:
    disconnect_account(session, company.id, account_id)
