"""Publish posts to Facebook Pages via the Graph API."""

from __future__ import annotations

import httpx

from app.schemas.content import GeneratedPostContent
from app.services.post_text import format_post_text

FACEBOOK_GRAPH = "https://graph.facebook.com/v21.0"


class FacebookPublishError(Exception):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def _parse_facebook_error(response: httpx.Response) -> str:
    try:
        payload = response.json()
        error = payload.get("error") or {}
        message = error.get("message")
        if message:
            return str(message)
    except ValueError:
        pass
    return response.text or f"HTTP {response.status_code}"


def publish_post(
    *,
    page_id: str,
    page_access_token: str,
    content: GeneratedPostContent,
    image_bytes: bytes | None = None,
    image_mime_type: str | None = None,
) -> str:
    text = format_post_text(content)
    if not text.strip():
        raise FacebookPublishError("Post text is empty.")

    with httpx.Client(timeout=60) as client:
        if image_bytes is not None:
            if not image_bytes:
                raise FacebookPublishError("Post image file is missing on the server.")
            response = client.post(
                f"{FACEBOOK_GRAPH}/{page_id}/photos",
                data={"message": text, "access_token": page_access_token},
                files={"source": ("post-image.jpg", image_bytes, image_mime_type or "image/jpeg")},
            )
        else:
            response = client.post(
                f"{FACEBOOK_GRAPH}/{page_id}/feed",
                data={"message": text, "access_token": page_access_token},
            )

        if response.is_error:
            raise FacebookPublishError(
                _parse_facebook_error(response),
                status_code=response.status_code,
            )

        payload = response.json()
        post_id = payload.get("id") or payload.get("post_id")
        if not post_id:
            raise FacebookPublishError("Facebook accepted the post but did not return a post id.")
        return str(post_id)
