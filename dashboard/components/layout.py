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


def page_header(title: str, subtitle: str | None = None) -> None:
    st.title(title)
    if subtitle:
        st.caption(subtitle)
    st.markdown("")


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
    st.markdown("### Welcome back")
    st.caption("Sign in to manage your content calendar and publishing queue.")
    st.markdown("")


def api_status_dot(status: str) -> None:
    if status == "ok":
        st.caption(f"API connected")
    else:
        st.caption(f"API {status}")
