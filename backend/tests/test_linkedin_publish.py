from app.schemas.content import GeneratedPostContent
from app.services.oauth import linkedin_publish
from app.services.post_text import format_post_text as build_post_text


def test_author_urn_organization() -> None:
    assert linkedin_publish.author_urn("12345", "organization") == "urn:li:organization:12345"


def test_person_urn_from_member_id() -> None:
    assert linkedin_publish.person_urn("abc123") == "urn:li:person:abc123"


def test_format_post_text_hook_body_hashtags() -> None:
    content = GeneratedPostContent(
        hook="Hello world",
        body="This is the body.",
        hashtags=["marketing", "saas"],
        platform="linkedin",
        post_type="professional",
    )
    text = linkedin_publish.format_post_text(content)
    assert "Hello world" in text
    assert "#marketing" in text


def test_build_post_text_shared_helper() -> None:
    content = GeneratedPostContent(
        hook="A",
        body="B",
        hashtags=[],
        platform="facebook",
        post_type="professional",
    )
    assert build_post_text(content) == "A\n\nB"
