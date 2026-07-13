import pytest
from fastapi import HTTPException

from app.services.company_scraper import validate_scrape_url


def test_validate_scrape_url_accepts_https():
    assert validate_scrape_url("https://example.com/about") == "https://example.com/about"


def test_validate_scrape_url_accepts_http():
    assert validate_scrape_url("http://example.com") == "http://example.com"


def test_validate_scrape_url_rejects_empty():
    with pytest.raises(HTTPException) as exc:
        validate_scrape_url("   ")
    assert exc.value.status_code == 400
    assert "required" in exc.value.detail.lower()


def test_validate_scrape_url_rejects_non_http_scheme():
    with pytest.raises(HTTPException) as exc:
        validate_scrape_url("ftp://example.com")
    assert exc.value.status_code == 400
    assert "http" in exc.value.detail.lower()


def test_validate_scrape_url_rejects_localhost():
    with pytest.raises(HTTPException) as exc:
        validate_scrape_url("http://localhost/about")
    assert exc.value.status_code == 400
    assert "internal" in exc.value.detail.lower() or "local" in exc.value.detail.lower()


def test_validate_scrape_url_rejects_private_ip():
    with pytest.raises(HTTPException) as exc:
        validate_scrape_url("http://192.168.1.1")
    assert exc.value.status_code == 400


def test_parse_profile_content_maps_fields():
    from app.services.company_scraper import _parse_profile_content

    result = _parse_profile_content(
        {
            "legal_name": "Acme Corp",
            "description": "We build widgets.",
            "industry": "Manufacturing",
            "website": None,
            "location": "Copenhagen",
            "target_audience": "B2B buyers",
            "products_services": "Widgets and parts",
        },
        "https://acme.example.com",
    )
    assert result.legal_name == "Acme Corp"
    assert result.website == "https://acme.example.com"
    assert result.industry == "Manufacturing"
