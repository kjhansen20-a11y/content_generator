import textwrap

import streamlit as st

from components.design import BORDER, RADIUS, SHADOW, SURFACE, TEXT, TEXT_MUTED


def _render_html(content: str) -> None:
    st.markdown(textwrap.dedent(content).strip(), unsafe_allow_html=True)


def inject_global_styles() -> None:
    _render_html(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {{
          font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }}

        .block-container {{
          padding-top: 1.5rem;
          max-width: 1100px;
        }}

        [data-testid="stSidebar"] {{
          background: {SURFACE};
          border-right: 1px solid {BORDER};
        }}

        [data-testid="stMetric"] {{
          background: {SURFACE};
          border: 1px solid {BORDER};
          border-radius: {RADIUS};
          padding: 0.85rem 1rem;
          box-shadow: {SHADOW};
        }}

        [data-testid="stMetricLabel"] {{
          font-size: 0.72rem !important;
          font-weight: 600 !important;
          text-transform: uppercase;
          letter-spacing: 0.04em;
          color: {TEXT_MUTED} !important;
        }}

        [data-testid="stMetricValue"] {{
          font-size: 1.6rem !important;
          font-weight: 700 !important;
          color: {TEXT} !important;
        }}
        </style>
        """
    )


def sidebar_brand() -> None:
    st.markdown("**Post Generator**")
    st.caption("AI content workspace")


def page_header(title: str, subtitle: str | None = None) -> None:
    st.title(title)
    if subtitle:
        st.caption(subtitle)
    st.markdown("")


def workflow_steps(steps: list[dict[str, str]], active_index: int = 0) -> None:
    for i, step in enumerate(steps):
        with st.container(border=True):
            title = f"Step {i + 1} · {step['title']}"
            if i == active_index:
                st.info(f"**{title}**")
            else:
                st.markdown(f"**{title}**")
            st.caption(step["description"])


def status_label(status: str) -> str:
    return status.replace("_", " ").upper()


def auth_hero() -> None:
    st.markdown("### Welcome back")
    st.caption("Sign in to manage your content calendar and publishing queue.")
    st.markdown("")


def api_status_dot(status: str) -> None:
    if status == "ok":
        st.caption(f"API connected")
    else:
        st.caption(f"API {status}")
