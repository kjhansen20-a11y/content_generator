import json
import uuid
from datetime import datetime, timedelta

from sqlmodel import Field, Session, SQLModel, select

from app.models.content import Platform
from app.services.token_crypto import decrypt_token, encrypt_token

PENDING_TTL_MINUTES = 30


class OAuthPendingConnection(SQLModel, table=True):
    """Temporary storage while the user picks which Facebook Page to connect."""

    __tablename__ = "oauth_pending_connections"

    id: str = Field(primary_key=True, max_length=36)
    company_id: int = Field(foreign_key="companies.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    platform: Platform
    payload_encrypted: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime


def create_pending_facebook_pages(
    session: Session,
    *,
    company_id: int,
    user_id: int,
    pages: list[dict],
) -> str:
    pending_id = str(uuid.uuid4())
    payload = json.dumps(
        [{"id": p["id"], "name": p.get("name"), "access_token": p["access_token"]} for p in pages]
    )
    pending = OAuthPendingConnection(
        id=pending_id,
        company_id=company_id,
        user_id=user_id,
        platform=Platform.facebook,
        payload_encrypted=encrypt_token(payload),
        expires_at=datetime.utcnow() + timedelta(minutes=PENDING_TTL_MINUTES),
    )
    session.add(pending)
    session.commit()
    return pending_id


def list_pending_facebook_pages(
    session: Session,
    *,
    pending_id: str,
    company_id: int,
    user_id: int,
) -> list[dict]:
    pending = session.get(OAuthPendingConnection, pending_id)
    if pending is None:
        raise ValueError("Pending connection not found")
    if pending.company_id != company_id or pending.user_id != user_id:
        raise ValueError("Pending connection does not belong to this user")
    if pending.expires_at < datetime.utcnow():
        raise ValueError("Pending connection expired — start Facebook connect again")
    raw = decrypt_token(pending.payload_encrypted)
    pages = json.loads(raw)
    return [{"id": str(p["id"]), "name": str(p.get("name") or "Facebook Page")} for p in pages]


def consume_pending_facebook_page(
    session: Session,
    *,
    pending_id: str,
    company_id: int,
    user_id: int,
    page_id: str,
) -> dict:
    pending = session.get(OAuthPendingConnection, pending_id)
    if pending is None:
        raise ValueError("Pending connection not found")
    if pending.company_id != company_id or pending.user_id != user_id:
        raise ValueError("Pending connection does not belong to this user")
    if pending.expires_at < datetime.utcnow():
        raise ValueError("Pending connection expired")
    raw = decrypt_token(pending.payload_encrypted)
    pages = json.loads(raw)
    match = next((p for p in pages if str(p["id"]) == str(page_id)), None)
    if match is None:
        raise ValueError("Selected page not found")
    session.delete(pending)
    session.commit()
    return {
        "external_id": str(match["id"]),
        "display_name": str(match.get("name") or "Facebook Page"),
        "access_token": str(match["access_token"]),
        "account_type": "page",
    }
