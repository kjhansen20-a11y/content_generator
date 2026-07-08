from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Post Generator"
    debug: bool = True

    database_url: str = "sqlite:///./app.db"

    jwt_secret: str = "change-me-to-a-long-random-string"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    platform_admin_email: str = ""

    uploads_dir: str = "uploads"
    max_upload_mb: int = 10

    # Public URLs (OAuth redirects)
    app_public_url: str = "http://127.0.0.1:8001"
    dashboard_url: str = "http://localhost:8501"

    # LinkedIn OAuth (https://www.linkedin.com/developers/)
    linkedin_client_id: str = ""
    linkedin_client_secret: str = ""

    # Meta / Facebook OAuth (https://developers.facebook.com/)
    facebook_app_id: str = ""
    facebook_app_secret: str = ""

    # Encrypt stored platform tokens (Fernet key; falls back to derived key from JWT_SECRET)
    oauth_token_encryption_key: str = ""

    @property
    def linkedin_redirect_uri(self) -> str:
        return f"{self.app_public_url.rstrip('/')}/api/v1/oauth/linkedin/callback"

    @property
    def facebook_redirect_uri(self) -> str:
        return f"{self.app_public_url.rstrip('/')}/api/v1/oauth/facebook/callback"

    @property
    def privacy_policy_url(self) -> str:
        return f"{self.app_public_url.rstrip('/')}/privacy"

    def linkedin_oauth_configured(self) -> bool:
        return bool(self.linkedin_client_id and self.linkedin_client_secret)

    def facebook_oauth_configured(self) -> bool:
        return bool(self.facebook_app_id and self.facebook_app_secret)


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reload_settings() -> Settings:
    """Clear cached settings (e.g. after .env changes)."""
    get_settings.cache_clear()
    return get_settings()
