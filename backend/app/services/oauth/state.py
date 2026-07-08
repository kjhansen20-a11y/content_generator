from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config import get_settings

OAUTH_STATE_TTL_MINUTES = 15


def create_oauth_state(
    *,
    company_id: int,
    user_id: int,
    platform: str,
    connection_kind: str = "profile",
) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=OAUTH_STATE_TTL_MINUTES)
    payload = {
        "typ": "oauth_state",
        "company_id": company_id,
        "user_id": user_id,
        "platform": platform,
        "connection_kind": connection_kind,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def parse_oauth_state(state: str) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(state, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Invalid or expired OAuth state") from exc
    if payload.get("typ") != "oauth_state":
        raise ValueError("Invalid OAuth state type")
    return {
        "company_id": int(payload["company_id"]),
        "user_id": int(payload["user_id"]),
        "platform": str(payload["platform"]),
        "connection_kind": str(payload.get("connection_kind") or "profile"),
    }
