import base64
import textwrap
from functools import lru_cache
from pathlib import Path

import streamlit as st

from components.design import BORDER, PRIMARY, RADIUS, SHADOW, STATUS_COLORS, SURFACE, TEXT, TEXT_MUTED
from styles.theme import build_global_css

LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "logo.png"
BRAND_LOGO_HEIGHT = 36

BRAND_MARK_SVG = """
<svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true">
  <rect width="32" height="32" rx="8" fill="#2563EB"/>
  <path d="M9 22V10h3.2l4.1 7.2L20.4 10H23.5v12h-2.6v-7.4l-3.8 6.6h-1.4l-3.8-6.6V22H9z" fill="#fff"/>
</svg>
"""


@lru_cache(maxsize=1)
def _brand_logo_data_uri() -> str | None:
    if not LOGO_PATH.is_file():
        return None
    encoded = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _brand_logo_img(*, height: int = BRAND_LOGO_HEIGHT, css_class: str = "pg-brand-logo") -> str:
    data_uri = _brand_logo_data_uri()
    if data_uri:
        return (
            f'<img class="{css_class}" src="{data_uri}" alt="" '
            f'height="{height}" aria-hidden="true" />'
        )
    return BRAND_MARK_SVG.strip()


def _render_html(content: str) -> None:
    html = textwrap.dedent(content).strip()
    if not html:
        return
    if html.lstrip().startswith("<style"):
        st.html(html)
    else:
        st.markdown(html, unsafe_allow_html=True)


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def inject_global_styles() -> None:
    _render_html(f"<style>{build_global_css()}</style>")


def page_header(
    title: str,
    subtitle: str | None = None,
    *,
    eyebrow: str | None = None,
) -> None:
    eyebrow_html = f'<p class="pg-page-eyebrow">{eyebrow}</p>' if eyebrow else ""
    subtitle_html = f'<p class="pg-page-subtitle">{subtitle}</p>' if subtitle else ""
    _render_html(
        f"""
        <div class="pg-page-header">
          {eyebrow_html}
          <h1 class="pg-page-title">{title}</h1>
          {subtitle_html}
        </div>
        """
    )


def section_title(title: str) -> None:
    _render_html(f'<h3 class="pg-section-title">{title}</h3>')


def status_badge(status: str) -> None:
    key = status.lower().replace(" ", "_")
    bg, fg = STATUS_COLORS.get(key, ("#F1F5F9", "#475569"))
    label = status.replace("_", " ").upper()
    _render_html(
        f'<span class="pg-status-badge" style="background:{bg};color:{fg};">{label}</span>'
    )


def workflow_steps(
    steps: list[dict[str, str]],
    *,
    completed: list[bool],
    active_index: int | None = None,
) -> None:
    for i, step in enumerate(steps):
        is_done = completed[i] if i < len(completed) else False
        is_active = active_index is not None and i == active_index and not is_done
        title = step["title"]
        description = step["description"]

        if is_done:
            state_class = "pg-workflow-step pg-workflow-step--done"
            marker = "✓"
            title_style = f"color: {TEXT_MUTED}; text-decoration: line-through;"
        elif is_active:
            state_class = "pg-workflow-step pg-workflow-step--active"
            marker = str(i + 1)
            title_style = f"color: {TEXT};"
        else:
            state_class = "pg-workflow-step"
            marker = str(i + 1)
            title_style = f"color: {TEXT};"

        _render_html(
            f"""
            <div class="{state_class}" style="
              border: 1px solid {BORDER};
              border-radius: {RADIUS};
              padding: 0.85rem 1rem;
              margin-bottom: 0.65rem;
              background: {SURFACE if not is_done else '#F8FAFC'};
              opacity: {'0.72' if is_done else '1'};
              box-shadow: {SHADOW};
            ">
              <div style="display:flex;gap:0.75rem;align-items:flex-start;">
                <div style="
                  min-width:1.6rem;height:1.6rem;border-radius:999px;
                  display:flex;align-items:center;justify-content:center;
                  font-size:0.8rem;font-weight:700;
                  background: {'#ECFDF5' if is_done else ('#EFF6FF' if is_active else '#F1F5F9')};
                  color: {'#047857' if is_done else ('#1D4ED8' if is_active else TEXT_MUTED)};
                ">{marker}</div>
                <div>
                  <div style="font-weight:600;{title_style}">Step {i + 1} · {title}</div>
                  <div style="font-size:0.85rem;color:{TEXT_MUTED};margin-top:0.2rem;">{description}</div>
                </div>
              </div>
            </div>
            """
        )


def status_label(status: str) -> str:
    return status.replace("_", " ").upper()


def auth_hero() -> None:
    logo = _brand_logo_img()
    _render_html(
        f'<div class="pg-auth-hero">'
        f'<div class="pg-brand">{logo} Kredesolutions</div>'
        f'<div class="pg-hero-badge">'
        f'<span class="pg-hero-badge-dot" aria-hidden="true"></span>'
        f"B2B content marketing platform"
        f"</div>"
        f'<h1 class="pg-auth-title">Post Generator</h1>'
        f'<p class="pg-auth-lead">'
        f"Sign in to plan content, generate on-brand posts with AI, "
        f"and publish to LinkedIn and Facebook."
        f"</p>"
        f"</div>"
    )


def auth_footer() -> None:
    _render_html(
        '<span class="pg-auth-footer">Operated by <strong>Kredesolutions</strong></span>'
    )


def api_status_dot(status: str) -> None:
    if status == "ok":
        st.caption("API connected")
    else:
        st.caption(f"API {status}")


def sidebar_brand() -> None:
    """Subtle Kredesolutions wordmark at top of st.sidebar (Streamlit's left nav panel)."""
    logo = _brand_logo_img(css_class="pg-sidebar-brand-logo")
    _render_html(
        f"""
        <div class="pg-sidebar-brand">
          <div class="pg-sidebar-brand-mark">{logo}</div>
          <div class="pg-sidebar-brand-text">
            <span class="pg-sidebar-brand-name">Kredesolutions</span>
            <span class="pg-sidebar-brand-product">Post Generator</span>
          </div>
        </div>
        """
    )


def sidebar_account(user: dict, company_name: str | None = None) -> None:
    email = _escape_html(user.get("email", ""))
    initial = email[0].upper() if email else "?"
    company_html = ""
    if company_name:
        company_html = (
            f'<span class="pg-sidebar-account-company">{_escape_html(company_name)}</span>'
        )
    admin_html = ""
    if user.get("is_platform_admin"):
        admin_html = '<span class="pg-sidebar-admin-badge">Platform admin</span>'
    _render_html(
        f"""
        <div class="pg-sidebar-account">
          <div class="pg-sidebar-account-row">
            <div class="pg-sidebar-avatar" aria-hidden="true">{initial}</div>
            <div class="pg-sidebar-account-meta">
              <span class="pg-sidebar-account-email">{email}</span>
              {company_html}
            </div>
          </div>
          {admin_html}
        </div>
        """
    )


def sidebar_section_label(title: str) -> None:
    _render_html(f'<p class="pg-sidebar-label">{_escape_html(title)}</p>')


MAIN_NAV_PAGES: tuple[str, ...] = (
    "Home",
    "Generate Post",
    "Publishing Queue",
    "Previous Posts",
    "Admin Dashboard",
)

SETTINGS_NAV_PAGES: tuple[str, ...] = (
    "Company Profile",
    "Brand Profile",
    "Connections",
    "Marketing Plan",
)

SETTINGS_NAV_LABEL = "Settings / Setup"


def _split_nav_options(nav_options: list[str]) -> tuple[list[str], list[str]]:
    main_pages = [page for page in MAIN_NAV_PAGES if page in nav_options]
    settings_pages = [page for page in SETTINGS_NAV_PAGES if page in nav_options]
    return main_pages, settings_pages


def _sync_nav_widget_keys(
    current: str,
    main_pages: list[str],
    settings_pages: list[str],
) -> None:
    """Keep radio widget keys aligned with st.session_state.page (OAuth, logout, etc.)."""
    if main_pages:
        if current in main_pages:
            st.session_state._pg_nav_main = current
            st.session_state.pop("_pg_nav_main_pick", None)
        else:
            st.session_state.pop("_pg_nav_main", None)

    if settings_pages:
        if current in settings_pages:
            st.session_state._pg_nav_settings = current
            st.session_state.pop("_pg_nav_settings_pick", None)
        else:
            st.session_state.pop("_pg_nav_settings", None)


def _navigate_from_main() -> None:
    st.session_state.page = st.session_state._pg_nav_main


def _navigate_from_main_pick() -> None:
    st.session_state.page = st.session_state._pg_nav_main_pick


def _navigate_from_settings() -> None:
    st.session_state.page = st.session_state._pg_nav_settings


def _navigate_from_settings_pick() -> None:
    st.session_state.page = st.session_state._pg_nav_settings_pick


def _render_sidebar_navigation(nav_options: list[str]) -> None:
    main_pages, settings_pages = _split_nav_options(nav_options)
    if not main_pages and not settings_pages:
        return

    sidebar_section_label("Navigation")
    current = st.session_state.get("page", main_pages[0] if main_pages else settings_pages[0])
    _sync_nav_widget_keys(current, main_pages, settings_pages)

    if main_pages:
        if current in main_pages:
            st.radio(
                "Main navigation",
                main_pages,
                key="_pg_nav_main",
                label_visibility="collapsed",
                on_change=_navigate_from_main,
            )
        else:
            st.radio(
                "Main navigation",
                main_pages,
                index=None,
                key="_pg_nav_main_pick",
                label_visibility="collapsed",
                on_change=_navigate_from_main_pick,
            )

    if settings_pages:
        settings_active = current in settings_pages
        with st.expander(SETTINGS_NAV_LABEL, expanded=settings_active):
            if settings_active:
                st.radio(
                    "Settings navigation",
                    settings_pages,
                    key="_pg_nav_settings",
                    label_visibility="collapsed",
                    on_change=_navigate_from_settings,
                )
            else:
                st.radio(
                    "Settings navigation",
                    settings_pages,
                    index=None,
                    key="_pg_nav_settings_pick",
                    label_visibility="collapsed",
                    on_change=_navigate_from_settings_pick,
                )


def render_authenticated_sidebar(
    user: dict,
    *,
    company_name: str | None = None,
    nav_options: list[str] | None = None,
    on_logout,
) -> None:
    """Render the authenticated left sidebar (st.sidebar) — nav, account, and sign-out."""
    with st.sidebar:
        sidebar_brand()
        sidebar_account(user, company_name)

        if nav_options:
            _render_sidebar_navigation(nav_options)

        _render_html('<div class="pg-sidebar-spacer" aria-hidden="true"></div>')
        st.button(
            "Log out",
            key="logout_button",
            use_container_width=True,
            on_click=on_logout,
        )
