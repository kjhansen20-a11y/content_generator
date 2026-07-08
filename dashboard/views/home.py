import streamlit as st

from api_client import ApiClient, ApiError
from components.layout import page_header, status_label, workflow_steps


def _count_by_status(items: list[dict], status: str) -> int:
    return sum(1 for item in items if item.get("status") == status)


def _go_to(page: str) -> None:
    st.session_state.nav_pending = page
    st.rerun()


def render_home_dashboard(
    client: ApiClient,
    token: str,
    company: dict,
    can_edit: bool,
) -> None:
    page_header(
        "Dashboard",
        f"Overview for {company['name']} — track drafts, approvals, and publishing.",
    )

    try:
        calendar = client.list_calendar(token, company["id"])
        queue = client.list_publishing_queue(token, company["id"])
        knowledge = client.list_knowledge(token, company["id"])
    except ApiError as exc:
        st.error(str(exc))
        return

    cols = st.columns(5)
    metrics = [
        ("Drafts", _count_by_status(calendar, "draft"), "Needs review"),
        ("Approved", _count_by_status(calendar, "approved"), "Ready to queue"),
        ("Queued", len(queue), "Awaiting publish"),
        ("Published", _count_by_status(calendar, "published"), "Live (mock)"),
        ("Knowledge", len(knowledge), "Context entries"),
    ]
    for col, (label, value, hint) in zip(cols, metrics):
        with col:
            st.metric(label=label, value=value, help=hint)

    col_workflow, col_recent = st.columns([1, 1])

    with col_workflow:
        st.subheader("Content workflow")
        workflow_steps(
            [
                {
                    "title": "Set up profiles & plan",
                    "description": "Company details, brand voice, knowledge base, and marketing plan.",
                },
                {
                    "title": "Generate posts",
                    "description": "Create AI drafts with images for each platform.",
                },
                {
                    "title": "Review & approve",
                    "description": "Edit and queue drafts right after generating.",
                },
                {
                    "title": "Publish",
                    "description": "Mock-publish from the queue; sent posts move to Previous Posts.",
                },
            ],
            active_index=1 if _count_by_status(calendar, "draft") else 0,
        )
        btn_cols = st.columns(3)
        with btn_cols[0]:
            if st.button("Marketing plan", use_container_width=True):
                _go_to("Marketing Plan")
        with btn_cols[1]:
            if st.button("Generate post", type="primary", use_container_width=True):
                _go_to("Generate Post")
        with btn_cols[2]:
            if st.button("Publishing queue", use_container_width=True):
                _go_to("Publishing Queue")

    with col_recent:
        st.subheader("Recent activity")
        with st.container(border=True):
            if calendar:
                for item in calendar[:5]:
                    status = status_label(item.get("status", "draft"))
                    hook = item.get("hook_preview") or "Untitled"
                    platform = str(item.get("platform", "")).title()
                    st.markdown(f"`{status}` · **{platform}** — {hook}")
            else:
                st.caption("No posts yet. Generate your first draft to get started.")

    if not can_edit:
        st.info("You have read-only access to this company.")
