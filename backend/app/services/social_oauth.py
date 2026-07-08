from dataclasses import dataclass
from datetime import datetime

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.config import get_settings
from app.models.content import Platform, PostType
from app.models.publishing import AccountStatus, ConnectedAccount
from app.models.tenancy import Company
from app.services.oauth import facebook as facebook_oauth
from app.services.oauth import linkedin as linkedin_oauth
from app.services.oauth.pending import (
    consume_pending_facebook_page,
    create_pending_facebook_pages,
    list_pending_facebook_pages,
)
from app.services.oauth.state import create_oauth_state, parse_oauth_state
from app.services.token_crypto import encrypt_token


@dataclass
class OAuthCallbackResult:
    account: ConnectedAccount | None = None
    pending_id: str | None = None
    platform: str | None = None


def oauth_start_url(
    *,
    company_id: int,
    user_id: int,
    platform: str,
    connection_kind: str = "profile",
) -> str:
    settings = get_settings()
    if platform == Platform.linkedin.value:
        if not settings.linkedin_oauth_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="LinkedIn is not available yet. Your platform administrator must enable the LinkedIn app.",
            )
        state = create_oauth_state(
            company_id=company_id,
            user_id=user_id,
            platform=platform,
            connection_kind=connection_kind,
        )
        return linkedin_oauth.linkedin_authorization_url(state)

    if platform == Platform.facebook.value:
        if not settings.facebook_oauth_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Facebook is not available yet. Your platform administrator must enable the Facebook app.",
            )
        state = create_oauth_state(
            company_id=company_id,
            user_id=user_id,
            platform=platform,
            connection_kind="page",
        )
        return facebook_oauth.facebook_authorization_url(state)

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported platform")


def oauth_handle_callback(
    session: Session,
    *,
    platform: str,
    code: str | None,
    state: str | None,
    error: str | None = None,
    error_description: str | None = None,
) -> OAuthCallbackResult:
    if error:
        message = error_description or error
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    if not code or not state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing OAuth code or state")

    try:
        state_data = parse_oauth_state(state)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if state_data["platform"] != platform:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth platform mismatch")

    company_id = state_data["company_id"]
    user_id = state_data["user_id"]
    connection_kind = state_data["connection_kind"]

    if platform == Platform.linkedin.value:
        tokens = linkedin_oauth.linkedin_exchange_code(code)
        profile = linkedin_oauth.linkedin_fetch_profile(tokens.access_token)
        account = _upsert_connected_account(
            session,
            company_id=company_id,
            user_id=user_id,
            platform=Platform.linkedin,
            profile_name=profile.display_name,
            external_id=profile.external_id,
            account_type="profile",
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            expires_at=tokens.expires_at,
            scopes=tokens.scopes,
        )
        for org in linkedin_oauth.linkedin_list_admin_organizations(tokens.access_token):
            _upsert_connected_account(
                session,
                company_id=company_id,
                user_id=user_id,
                platform=Platform.linkedin,
                profile_name=org.display_name,
                external_id=org.external_id,
                account_type="organization",
                access_token=tokens.access_token,
                refresh_token=tokens.refresh_token,
                expires_at=tokens.expires_at,
                scopes=tokens.scopes,
            )
        return OAuthCallbackResult(account=account, platform=platform)

    if platform == Platform.facebook.value:
        tokens = facebook_oauth.facebook_exchange_code(code)
        pages = facebook_oauth.facebook_list_pages(tokens.access_token)
        if len(pages) == 1:
            page = pages[0]
            account = _upsert_connected_account(
                session,
                company_id=company_id,
                user_id=user_id,
                platform=Platform.facebook,
                profile_name=str(page.get("name") or "Facebook Page"),
                external_id=str(page["id"]),
                account_type="page",
                access_token=str(page["access_token"]),
                refresh_token=None,
                expires_at=tokens.expires_at,
                scopes=tokens.scopes,
            )
            return OAuthCallbackResult(account=account, platform=platform)

        pending_id = create_pending_facebook_pages(
            session,
            company_id=company_id,
            user_id=user_id,
            pages=pages,
        )
        return OAuthCallbackResult(pending_id=pending_id, platform=platform)

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported platform")


def complete_facebook_page_connection(
    session: Session,
    *,
    company_id: int,
    user_id: int,
    pending_id: str,
    page_id: str,
) -> ConnectedAccount:
    try:
        page = consume_pending_facebook_page(
            session,
            pending_id=pending_id,
            company_id=company_id,
            user_id=user_id,
            page_id=page_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return _upsert_connected_account(
        session,
        company_id=company_id,
        user_id=user_id,
        platform=Platform.facebook,
        profile_name=page["display_name"],
        external_id=page["external_id"],
        account_type="page",
        access_token=page["access_token"],
        refresh_token=None,
        expires_at=None,
        scopes=",".join(facebook_oauth.FACEBOOK_SCOPES),
    )


def get_pending_facebook_pages(
    session: Session,
    *,
    company_id: int,
    user_id: int,
    pending_id: str,
) -> list[dict]:
    try:
        return list_pending_facebook_pages(
            session,
            pending_id=pending_id,
            company_id=company_id,
            user_id=user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


def _upsert_connected_account(
    session: Session,
    *,
    company_id: int,
    user_id: int,
    platform: Platform,
    profile_name: str,
    external_id: str,
    account_type: str,
    access_token: str,
    refresh_token: str | None,
    expires_at: datetime | None,
    scopes: str,
) -> ConnectedAccount:
    """Store tokens for the user who authorized — each team member connects their own profile/page."""
    query = select(ConnectedAccount).where(
        ConnectedAccount.company_id == company_id,
        ConnectedAccount.platform == platform,
        ConnectedAccount.is_mock == False,  # noqa: E712
        ConnectedAccount.external_account_id == external_id,
    )
    if account_type == "profile":
        query = query.where(ConnectedAccount.connected_by_user_id == user_id)

    account = session.exec(query).first()
    now = datetime.utcnow()

    if account is None:
        account = ConnectedAccount(
            company_id=company_id,
            platform=platform,
            account_name=profile_name,
            is_mock=False,
            status=AccountStatus.active,
        )

    account.account_name = profile_name
    account.external_account_id = external_id
    account.account_type = account_type
    account.access_token_encrypted = encrypt_token(access_token)
    account.refresh_token_encrypted = (
        encrypt_token(refresh_token) if refresh_token else None
    )
    account.token_expires_at = expires_at.replace(tzinfo=None) if expires_at else None
    account.scopes = scopes
    account.connected_by_user_id = user_id
    account.status = AccountStatus.active
    account.updated_at = now

    session.add(account)
    session.commit()
    session.refresh(account)
    return account


def disconnect_account(session: Session, company_id: int, account_id: int) -> None:
    account = session.get(ConnectedAccount, account_id)
    if account is None or account.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connected account not found")
    if account.is_mock:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot disconnect mock accounts")

    account.status = AccountStatus.inactive
    account.access_token_encrypted = None
    account.refresh_token_encrypted = None
    account.token_expires_at = None
    account.updated_at = datetime.utcnow()
    session.add(account)
    session.commit()


def _pick_linkedin_organization(
    session: Session,
    company_id: int,
    user_id: int,
    accounts: list[ConnectedAccount],
) -> ConnectedAccount | None:
    if not accounts:
        return None
    if len(accounts) == 1:
        return accounts[0]

    company = session.get(Company, company_id)
    if company and company.name:
        company_name = company.name.lower()
        for account in accounts:
            page_name = account.account_name.lower()
            if company_name in page_name or page_name in company_name:
                return account

    return sorted(accounts, key=lambda a: a.account_name)[0]


def get_active_real_account(
    session: Session,
    company_id: int,
    platform: Platform,
    *,
    user_id: int | None = None,
    post_type: str | PostType | None = None,
) -> ConnectedAccount | None:
    """Resolve which connected account to publish with (profile vs company page)."""
    if platform == Platform.linkedin and user_id is not None:
        use_profile = post_type in (PostType.personal, PostType.personal.value)
        account_type = "profile" if use_profile else "organization"
        query = select(ConnectedAccount).where(
            ConnectedAccount.company_id == company_id,
            ConnectedAccount.platform == platform,
            ConnectedAccount.is_mock == False,  # noqa: E712
            ConnectedAccount.status == AccountStatus.active,
            ConnectedAccount.connected_by_user_id == user_id,
            ConnectedAccount.account_type == account_type,
            ConnectedAccount.access_token_encrypted.is_not(None),
        )
        if account_type == "organization":
            org_accounts = list(session.exec(query).all())
            return _pick_linkedin_organization(session, company_id, user_id, org_accounts)
        return session.exec(query).first()

    return session.exec(
        select(ConnectedAccount).where(
            ConnectedAccount.company_id == company_id,
            ConnectedAccount.platform == platform,
            ConnectedAccount.is_mock == False,  # noqa: E712
            ConnectedAccount.status == AccountStatus.active,
            ConnectedAccount.access_token_encrypted.is_not(None),
        )
        .order_by(ConnectedAccount.updated_at.desc())
    ).first()
