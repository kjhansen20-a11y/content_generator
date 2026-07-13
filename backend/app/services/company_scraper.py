"""Fetch company website content and extract profile fields with AI."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from fastapi import HTTPException, status
from sqlmodel import Session

from app.models.tenancy import Company
from app.schemas.profile import CompanyProfileUpdate
from app.services.openai_client import chat_json
from app.services.prompt_builder import get_active_prompt_body
from app.services.text_extract import MAX_EXTRACT_CHARS

USER_AGENT = "PostGenerator/1.0 (+company-profile-import)"
FETCH_TIMEOUT = 30.0
MAX_RESPONSE_BYTES = 2_000_000

BLOCKED_HOSTNAMES = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
}

PRIVATE_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def _is_blocked_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return True
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
        return True
    return any(ip in network for network in PRIVATE_NETWORKS)


def validate_scrape_url(url: str) -> str:
    """Validate and normalize a URL for scraping."""
    url = url.strip()
    if not url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URL is required.")

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only http and https URLs are supported.",
        )

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL must include a valid host.",
        )

    if hostname in BLOCKED_HOSTNAMES or hostname.endswith(".localhost"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Local and internal URLs are not allowed.",
        )

    try:
        addrinfos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not resolve host: {hostname}",
        ) from exc

    for info in addrinfos:
        ip = info[4][0]
        if _is_blocked_ip(ip):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="URLs pointing to private or internal networks are not allowed.",
            )

    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path or ''}"
    if parsed.query:
        normalized += f"?{parsed.query}"
    return normalized


def fetch_page_text(url: str) -> tuple[str, str]:
    """Fetch URL and extract readable text. Returns (page_title, body_text)."""
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"}
    try:
        with httpx.Client(timeout=FETCH_TIMEOUT, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The website took too long to respond. Try again or fill in the profile manually.",
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                f"The website returned HTTP {exc.response.status_code}. "
                "Check the URL and try again."
            ),
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not reach the website ({exc.__class__.__name__}). Check the URL and try again.",
        ) from exc

    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type and "application/xhtml" not in content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The URL did not return an HTML page. "
                "Provide a public website homepage or about page."
            ),
        )

    raw = response.content[:MAX_RESPONSE_BYTES]
    soup = BeautifulSoup(raw, "html.parser")

    for tag in soup(["script", "style", "noscript", "svg", "iframe"]):
        tag.decompose()

    title = (soup.title.string or "").strip() if soup.title and soup.title.string else ""

    meta_parts: list[str] = []
    for attrs in (
        {"property": "og:description"},
        {"name": "description"},
        {"property": "og:site_name"},
    ):
        tag = soup.find("meta", attrs=attrs)
        content = tag.get("content", "").strip() if tag else ""
        if content:
            meta_parts.append(content)

    body_text = soup.get_text(separator="\n", strip=True)
    combined = "\n\n".join(part for part in [title, *meta_parts, body_text] if part)
    combined = "\n".join(line for line in combined.splitlines() if line.strip())

    if len(combined) < 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Not enough readable content on this page. "
                "Try your homepage or an About page, or fill in manually."
            ),
        )

    return title, combined[:MAX_EXTRACT_CHARS]


def _optional_str(data: dict, key: str, max_len: int | None = None) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if max_len is not None:
        text = text[:max_len]
    return text


def _parse_profile_content(data: dict, source_url: str) -> CompanyProfileUpdate:
    website = _optional_str(data, "website", 512) or source_url[:512]
    return CompanyProfileUpdate(
        legal_name=_optional_str(data, "legal_name", 255),
        description=_optional_str(data, "description"),
        industry=_optional_str(data, "industry", 255),
        website=website,
        location=_optional_str(data, "location", 255),
        target_audience=_optional_str(data, "target_audience"),
        products_services=_optional_str(data, "products_services"),
    )


def scrape_company_profile(
    session: Session,
    company: Company,
    url: str,
) -> CompanyProfileUpdate:
    normalized_url = validate_scrape_url(url)
    page_title, page_text = fetch_page_text(normalized_url)

    system_prompt = get_active_prompt_body(session, "company_profile_scrape")
    user_prompt = (
        f"Source URL: {normalized_url}\n"
        f"Page title: {page_title or '(none)'}\n\n"
        f"Website content:\n{page_text}"
    )

    result = chat_json(
        session,
        company_id=company.id,
        operation="scrape_company_profile",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    profile_data = _parse_profile_content(result.content, normalized_url)
    if not any(
        [
            profile_data.legal_name,
            profile_data.description,
            profile_data.industry,
            profile_data.target_audience,
            profile_data.products_services,
        ]
    ):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Could not extract enough company information from this page. "
                "Try a different URL or fill in manually."
            ),
        )

    return profile_data
