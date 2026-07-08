"""Print LinkedIn OAuth setup checklist and verify configuration."""

from app.config import get_settings


def main() -> None:
    settings = get_settings()
    print("=== Post Generator — LinkedIn OAuth ===\n")
    print("Redirect URI (add this EXACTLY in LinkedIn Developer Portal -> Auth):")
    print(f"  {settings.linkedin_redirect_uri}\n")
    print("Required LinkedIn products (Products tab):")
    print("  - Sign In with LinkedIn using OpenID Connect")
    print("  - Share on LinkedIn\n")
    print("Scopes used by this app:")
    print("  openid profile email w_member_social\n")
    print("Configuration status:")
    print(f"  LINKEDIN_CLIENT_ID:     {'set' if settings.linkedin_client_id else 'MISSING'}")
    print(f"  LINKEDIN_CLIENT_SECRET: {'set' if settings.linkedin_client_secret else 'MISSING'}")
    print(f"  APP_PUBLIC_URL:         {settings.app_public_url}")
    print(f"  DASHBOARD_URL:          {settings.dashboard_url}")
    print(f"  Ready:                  {settings.linkedin_oauth_configured()}\n")
    if not settings.linkedin_oauth_configured():
        print("Next: add credentials to backend/.env and restart the API.")


if __name__ == "__main__":
    main()
