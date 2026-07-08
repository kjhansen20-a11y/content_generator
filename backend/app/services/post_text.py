"""Format generated post content for social platform APIs."""

from app.schemas.content import GeneratedPostContent

POST_CHAR_LIMIT = 3000


def format_post_text(content: GeneratedPostContent) -> str:
    parts: list[str] = []
    if content.hook and content.hook.strip():
        parts.append(content.hook.strip())
    if content.body and content.body.strip():
        parts.append(content.body.strip())
    text = "\n\n".join(parts)
    if content.hashtags:
        tags = " ".join(f"#{tag.lstrip('#').strip()}" for tag in content.hashtags if tag and tag.strip())
        if tags:
            text = f"{text}\n\n{tags}" if text else tags
    if not text.strip():
        return ""
    if len(text) > POST_CHAR_LIMIT:
        text = text[: POST_CHAR_LIMIT - 1].rstrip() + "…"
    return text
