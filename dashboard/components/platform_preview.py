import html
import re

import streamlit.components.v1 as components

_PREVIEW_STYLES = """
<style>
  .pg-wrap { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
  .pg-card { background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; max-width: 555px; margin: 0 auto; }
  .pg-muted { color: #666; font-size: 12px; }
  .pg-header { display: flex; gap: 10px; padding: 12px 16px 8px; align-items: flex-start; }
  .pg-avatar { width: 48px; height: 48px; border-radius: 50%; background: #0a66c2; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 16px; flex-shrink: 0; }
  .pg-avatar.fb { background: #1877f2; }
  .pg-avatar.ig { background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888); }
  .pg-name { font-weight: 600; font-size: 14px; color: #000; line-height: 1.3; }
  .pg-sub { font-size: 12px; color: #666; line-height: 1.3; }
  .pg-body { padding: 0 16px 12px; font-size: 14px; color: rgba(0,0,0,0.9); line-height: 1.45; white-space: pre-wrap; word-wrap: break-word; }
  .pg-see-more { color: #666; cursor: default; }
  .pg-image { background: #f3f2ef; border-top: 1px solid #eee; border-bottom: 1px solid #eee; min-height: 200px; display: flex; align-items: center; justify-content: center; color: #666; font-size: 13px; padding: 24px; text-align: center; }
  .pg-image-img { width: 100%; display: block; max-height: 360px; object-fit: cover; border-top: 1px solid #eee; border-bottom: 1px solid #eee; }
  .pg-image.ig { min-height: 280px; background: #fafafa; }
  .pg-engagement { padding: 8px 16px; border-top: 1px solid #eee; display: flex; justify-content: space-around; color: #666; font-size: 13px; font-weight: 600; }
  .pg-engagement span { padding: 8px 12px; }
  .pg-ig-caption { padding: 12px 16px 16px; font-size: 14px; line-height: 1.45; white-space: pre-wrap; }
  .pg-ig-user { font-weight: 600; margin-right: 6px; }
  .pg-label { text-align: center; font-size: 11px; color: #888; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
</style>
"""


def _initials(name: str) -> str:
    parts = [p for p in name.split() if p]
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return name[:2].upper() if name else "CO"


def _build_post_text(content: dict) -> str:
    hook = (content.get("hook") or "").strip()
    body = (content.get("body") or "").strip()
    hashtags = content.get("hashtags") or []

    parts: list[str] = []
    if hook:
        parts.append(hook)
    if body:
        parts.append(body)
    text = "\n\n".join(parts)

    if hashtags:
        tags = " ".join(f"#{str(t).lstrip('#')}" for t in hashtags if str(t).strip())
        if tags:
            text = f"{text}\n\n{tags}" if text else tags
    return text


def _truncate_linkedin(text: str, limit: int = 210) -> tuple[str, bool]:
    if len(text) <= limit:
        return text, False
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut.rstrip(), True


def _escape(text: str) -> str:
    return html.escape(text)


def _image_block(alt_text: str | None, platform: str) -> str:
    if not alt_text or not alt_text.strip():
        return ""
    css = "pg-image ig" if platform == "instagram" else "pg-image"
    return f'<div class="{css}">📷 {_escape(alt_text.strip())}</div>'


def _image_html(
    image_base64: str | None,
    image_mime: str | None,
    alt_text: str | None,
    platform: str,
) -> str:
    if image_base64 and image_mime:
        alt = _escape(alt_text or "Post image")
        return (
            f'<img class="pg-image-img" src="data:{image_mime};base64,{image_base64}" '
            f'alt="{alt}" />'
        )
    return _image_block(alt_text, platform)


def _linkedin_preview(
    company_name: str, content: dict, image_base64: str | None = None, image_mime: str | None = None
) -> str:
    text = _build_post_text(content)
    display, truncated = _truncate_linkedin(text)
    body_html = _escape(display)
    if truncated:
        body_html += ' <span class="pg-see-more">…see more</span>'

    image = _image_html(image_base64, image_mime, content.get("alt_text"), "linkedin")
    initials = _initials(company_name)

    return f"""
    <div class="pg-wrap">
      <div class="pg-label">LinkedIn feed preview (approximate)</div>
      <div class="pg-card">
        <div class="pg-header">
          <div class="pg-avatar">{initials}</div>
          <div>
            <div class="pg-name">{_escape(company_name)}</div>
            <div class="pg-sub">Company · 1h · 🌐</div>
          </div>
        </div>
        <div class="pg-body">{body_html}</div>
        {image}
        <div class="pg-engagement">
          <span>👍 Like</span><span>💬 Comment</span><span>↗ Repost</span><span>✉ Send</span>
        </div>
      </div>
    </div>
    """


def _facebook_preview(
    company_name: str, content: dict, image_base64: str | None = None, image_mime: str | None = None
) -> str:
    text = _build_post_text(content)
    image = _image_html(image_base64, image_mime, content.get("alt_text"), "facebook")
    initials = _initials(company_name)

    return f"""
    <div class="pg-wrap">
      <div class="pg-label">Facebook feed preview (approximate)</div>
      <div class="pg-card">
        <div class="pg-header">
          <div class="pg-avatar fb">{initials}</div>
          <div>
            <div class="pg-name">{_escape(company_name)}</div>
            <div class="pg-sub">Just now · 🌐</div>
          </div>
        </div>
        <div class="pg-body">{_escape(text)}</div>
        {image}
        <div class="pg-engagement">
          <span>👍 Like</span><span>💬 Comment</span><span>↗ Share</span>
        </div>
      </div>
    </div>
    """


def _instagram_preview(
    company_name: str, content: dict, image_base64: str | None = None, image_mime: str | None = None
) -> str:
    text = _build_post_text(content)
    if image_base64 and image_mime:
        alt = _escape(content.get("alt_text") or "Post image")
        image_html = (
            f'<img class="pg-image-img" src="data:{image_mime};base64,{image_base64}" alt="{alt}" />'
        )
    elif content.get("alt_text"):
        image_html = f'<div class="pg-image ig">📷 {_escape(content["alt_text"].strip())}</div>'
    else:
        image_html = '<div class="pg-image ig">Image preview</div>'
    username = re.sub(r"[^a-z0-9_]", "", company_name.lower().replace(" ", "_")) or "company"

    return f"""
    <div class="pg-wrap">
      <div class="pg-label">Instagram feed preview (approximate)</div>
      <div class="pg-card">
        <div class="pg-header">
          <div class="pg-avatar ig">{_initials(company_name)}</div>
          <div>
            <div class="pg-name">{_escape(username)}</div>
            <div class="pg-sub">Original audio</div>
          </div>
        </div>
        {image_html}
        <div class="pg-ig-caption">
          <span class="pg-ig-user">{_escape(username)}</span>{_escape(text)}
        </div>
        <div class="pg-engagement">
          <span>♡</span><span>💬</span><span>✈</span>
        </div>
      </div>
    </div>
    """


def build_platform_preview_html(
    platform: str,
    company_name: str,
    content: dict,
    image_base64: str | None = None,
    image_mime: str | None = None,
) -> str:
    platform = (platform or "linkedin").lower()
    if platform == "facebook":
        inner = _facebook_preview(company_name, content, image_base64, image_mime)
    elif platform == "instagram":
        inner = _instagram_preview(company_name, content, image_base64, image_mime)
    else:
        inner = _linkedin_preview(company_name, content, image_base64, image_mime)
    return _PREVIEW_STYLES + inner


def render_platform_preview(
    platform: str,
    company_name: str,
    content: dict,
    height: int = 520,
    image_base64: str | None = None,
    image_mime: str | None = None,
) -> None:
    html_doc = build_platform_preview_html(
        platform, company_name, content, image_base64=image_base64, image_mime=image_mime
    )
    components.html(html_doc, height=height, scrolling=False)
