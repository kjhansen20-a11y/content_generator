from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse

from app.config import get_settings

router = APIRouter(tags=["public"])

_STATIC = Path(__file__).resolve().parent.parent / "static"


@router.get("/", response_class=HTMLResponse)
def home() -> str:
    settings = get_settings()
    return f"""<!DOCTYPE html>
<html><head><title>Post Generator API</title></head>
<body style="font-family:system-ui;max-width:600px;margin:3rem auto;padding:0 1rem">
  <h1>Post Generator</h1>
  <p>API is running.</p>
  <ul>
    <li><a href="/health">Health</a></li>
    <li><a href="/docs">API documentation</a></li>
    <li><a href="/privacy">Privacy policy</a></li>
  </ul>
  <p>App: <a href="{settings.dashboard_url}">{settings.dashboard_url}</a></p>
</body></html>"""


@router.get("/privacy")
def privacy_policy() -> FileResponse:
    return FileResponse(_STATIC / "privacy.html", media_type="text/html")
