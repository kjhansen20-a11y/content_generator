import streamlit as st

from api_client import ApiClient, ApiError
from components.layout import page_header, section_title, status_badge, workflow_steps

WORKFLOW_STEPS = [
    {
        "title": "Company Profile",
        "description": "In Settings / Setup, add business context so AI drafts match your company.",
    },
    {
        "title": "Brand Profile",
        "description": "In Settings / Setup, define brand voice and tone for on-brand content.",
    },
    {
        "title": "Connections",
        "description": "In Settings / Setup, connect LinkedIn or Facebook so Post Generator can publish on your behalf.",
    },
    {
        "title": "Marketing Plan",
        "description": "In Settings / Setup, define goals, content pillars, and a posting schedule.",
    },
    {
        "title": "Generate your first post",
        "description": "Create an AI draft with platform-specific copy and optional image.",
    },
    {
        "title": "Review and queue your first post",
        "description": "Edit, approve, and add the draft to the publishing queue.",
    },
    {
        "title": "First post published",
        "description": "Publish from the queue to complete your first live post.",
    },
]


def _count_by_status(items: list[dict], status: str) -> int:
    return sum(1 for item in items if item.get("status") == status)


def _filled(value: object) -> bool:
    return bool(value and str(value).strip())


def _company_profile_complete(profile: dict) -> bool:
    key_fields = [
        profile.get("legal_name"),
        profile.get("industry"),
        profile.get("description"),
        profile.get("target_audience"),
    ]
    return sum(1 for field in key_fields if _filled(field)) >= 2


def _brand_profile_complete(profile: dict) -> bool:
    return _filled(profile.get("tone_of_voice")) or _filled(profile.get("brand_voice_description"))


def _workflow_completion(
    *,
    company_profile: dict,
    brand_profile: dict,
    accounts: list[dict],
    active_plan: dict | None,
    calendar: list[dict],
    queue: list[dict],
) -> list[bool]:
    company_done = _company_profile_complete(company_profile)
    brand_done = _brand_profile_complete(brand_profile)
    connections_done = any(
        not account.get("is_mock") and account.get("status") == "active" for account in accounts
    )
    plan_done = active_plan is not None
    generated_done = len(calendar) > 0
    queued_done = (
        len(queue) > 0
        or any(item.get("status") in ("approved", "queued", "published") for item in calendar)
    )
    published_done = any(item.get("status") == "published" for item in calendar)
    return [
        company_done,
        brand_done,
        connections_done,
        plan_done,
        generated_done,
        queued_done,
        published_done,
    ]


def _first_incomplete_index(completed: list[bool]) -> int | None:
    for index, is_done in enumerate(completed):
        if not is_done:
            return index
    return None


def render_home_dashboard(
    client: ApiClient,
    token: str,
    company: dict,
    can_edit: bool,
) -> None:
    page_header(
        "Dashboard",
        f"Overview for {company['name']} — track drafts, queue, and published posts.",
        eyebrow="Overview",
    )

    try:
        calendar = client.list_calendar(token, company["id"])
        queue = client.list_publishing_queue(token, company["id"])
        company_profile = client.get_company_profile(token, company["id"])
        brand_profile = client.get_brand_profile(token, company["id"])
        accounts = client.list_connected_accounts(token, company["id"])
        active_plan = client.get_active_marketing_plan(token, company["id"])
    except ApiError as exc:
        st.error(str(exc))
        return

    completed = _workflow_completion(
        company_profile=company_profile,
        brand_profile=brand_profile,
        accounts=accounts,
        active_plan=active_plan,
        calendar=calendar,
        queue=queue,
    )
    onboarding_complete = all(completed)
    active_step = _first_incomplete_index(completed)

    cols = st.columns(3)
    metrics = [
        ("Drafts", _count_by_status(calendar, "draft"), "Posts awaiting review"),
        ("Queued", len(queue), "Posts awaiting publish"),
        ("Published", _count_by_status(calendar, "published"), "Live posts"),
    ]
    for col, (label, value, hint) in zip(cols, metrics):
        with col:
            st.metric(label=label, value=value, help=hint)

    if not onboarding_complete:
        section_title("Setup guide")
        st.caption("Complete each step to get your first post live.")
        workflow_steps(WORKFLOW_STEPS, completed=completed, active_index=active_step)
        st.markdown("")

    section_title("Recent activity")
    with st.container(border=True):
        if calendar:
            for item in calendar[:5]:
                status = item.get("status", "draft")
                hook = item.get("hook_preview") or "Untitled"
                platform = str(item.get("platform", "")).title()
                col_badge, col_text = st.columns([1, 5])
                with col_badge:
                    status_badge(status)
                with col_text:
                    st.markdown(f"**{platform}** — {hook}")
        else:
            st.caption("No posts yet. Generate your first draft to get started.")

    if not can_edit:
        st.info("You have read-only access to this company.")
