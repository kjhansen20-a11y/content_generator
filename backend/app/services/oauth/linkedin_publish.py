"""Publish posts to LinkedIn via the UGC Posts API (w_member_social)."""

from __future__ import annotations

import httpx

from app.schemas.content import GeneratedPostContent
from app.services.post_text import POST_CHAR_LIMIT
from app.services.post_text import format_post_text as build_post_text

LINKEDIN_UGC_POSTS_URL = "https://api.linkedin.com/v2/ugcPosts"
LINKEDIN_ASSETS_URL = "https://api.linkedin.com/v2/assets"
LINKEDIN_POST_CHAR_LIMIT = POST_CHAR_LIMIT


class LinkedInPublishError(Exception):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def author_urn(external_account_id: str, account_type: str | None = None) -> str:
    member_id = external_account_id.strip()
    kind = (account_type or "profile").lower()
    if kind == "organization":
        if member_id.startswith("urn:li:organization:"):
            return member_id
        return f"urn:li:organization:{member_id}"
    return person_urn(member_id)


def person_urn(external_account_id: str) -> str:
    member_id = external_account_id.strip()
    if member_id.startswith("urn:li:person:"):
        return member_id
    return f"urn:li:person:{member_id}"


def format_post_text(content: GeneratedPostContent) -> str:
    text = build_post_text(content)
    if not text.strip():
        raise LinkedInPublishError("Post text is empty.")
    return text


def _linkedin_json_headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }


def _parse_linkedin_error(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text or f"HTTP {response.status_code}"
    message = payload.get("message")
    if message:
        return str(message)
    service_error = payload.get("serviceErrorCode")
    if service_error:
        return f"LinkedIn service error {service_error}"
    return str(payload)


def _upload_image(access_token: str, owner_urn: str, image_bytes: bytes, mime_type: str) -> str:
    register_payload = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": owner_urn,
            "serviceRelationships": [
                {
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent",
                }
            ],
        }
    }
    with httpx.Client(timeout=60) as client:
        register_response = client.post(
            f"{LINKEDIN_ASSETS_URL}?action=registerUpload",
            headers=_linkedin_json_headers(access_token),
            json=register_payload,
        )
        if register_response.is_error:
            raise LinkedInPublishError(
                _parse_linkedin_error(register_response),
                status_code=register_response.status_code,
            )

        register_data = register_response.json()["value"]
        asset_urn = register_data["asset"]
        upload_info = register_data["uploadMechanism"][
            "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
        ]
        upload_url = upload_info["uploadUrl"]
        upload_headers = upload_info.get("headers", {})

        put_headers = {"Authorization": f"Bearer {access_token}", **upload_headers}
        if "Content-Type" not in put_headers:
            put_headers["Content-Type"] = mime_type

        upload_response = client.put(upload_url, headers=put_headers, content=image_bytes)
        if upload_response.is_error:
            raise LinkedInPublishError(
                f"Image upload failed: {upload_response.text or upload_response.status_code}",
                status_code=upload_response.status_code,
            )

    return asset_urn


def publish_post(
    *,
    access_token: str,
    external_account_id: str,
    content: GeneratedPostContent,
    image_bytes: bytes | None = None,
    image_mime_type: str | None = None,
    account_type: str = "profile",
) -> str:
    """Create a LinkedIn post and return the external post id."""
    author = author_urn(external_account_id, account_type)
    text = format_post_text(content)

    share_content: dict = {
        "shareCommentary": {"text": text},
        "shareMediaCategory": "NONE",
    }

    if image_bytes is not None:
        if not image_bytes:
            raise LinkedInPublishError("Post image file is missing on the server.")
        mime = image_mime_type or "image/jpeg"
        asset_urn = _upload_image(access_token, author, image_bytes, mime)
        share_content = {
            "shareCommentary": {"text": text},
            "shareMediaCategory": "IMAGE",
            "media": [
                {
                    "status": "READY",
                    "description": {"text": content.alt_text or "Post image"},
                    "media": asset_urn,
                    "title": {"text": "Post image"},
                }
            ],
        }

    payload = {
        "author": author,
        "lifecycleState": "PUBLISHED",
        "specificContent": {"com.linkedin.ugc.ShareContent": share_content},
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    with httpx.Client(timeout=60) as client:
        response = client.post(
            LINKEDIN_UGC_POSTS_URL,
            headers=_linkedin_json_headers(access_token),
            json=payload,
        )
        if response.is_error:
            raise LinkedInPublishError(
                _parse_linkedin_error(response),
                status_code=response.status_code,
            )

        post_id = response.headers.get("X-Restli-Id")
        if not post_id:
            try:
                post_id = response.json().get("id")
            except ValueError:
                post_id = None
        if not post_id:
            raise LinkedInPublishError("LinkedIn accepted the post but did not return a post id.")
        return str(post_id)
