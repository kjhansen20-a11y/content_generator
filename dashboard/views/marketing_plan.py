from datetime import date

import streamlit as st

from api_client import ApiClient, ApiError
from components.layout import page_header
from components.plan_visual import render_plan_visual

WEEKDAYS_FULL = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
PLAN_UPLOAD_EXTENSIONS = ("txt", "md", "csv", "pdf")
PLATFORM_OPTIONS = ["linkedin", "facebook", "instagram"]


def render_marketing_plan(client: ApiClient, token: str, company_id: int, can_edit: bool) -> None:
    page_header(
        "Marketing Plan",
        "Build a strategy with AI from your expectations and keywords, then visualize pillars and posting schedule.",
    )

    try:
        plans = client.list_marketing_plans(token, company_id)
        active_plan = client.get_active_marketing_plan(token, company_id)
        pillars = client.list_content_pillars(token, company_id)
        rules = client.list_posting_rules(token, company_id)
    except ApiError as exc:
        if exc.status_code == 404:
            st.error("Marketing plan API unavailable. Restart the backend on port 8001.")
        else:
            st.error(str(exc))
        return

    has_plan = bool(active_plan or plans)

    if has_plan and active_plan:
        render_plan_visual(active_plan, pillars, rules)
        st.divider()

    if not has_plan:
        _render_get_started(client, token, company_id, can_edit)
        return

    tab_build, tab_overview, tab_pillars, tab_schedule = st.tabs(
        ["AI builder", "Overview", "Pillars", "Schedule"]
    )

    with tab_build:
        _render_ai_builder(client, token, company_id, can_edit)
        if can_edit:
            st.divider()
            _render_manual_options(client, token, company_id, expanded=False)

    with tab_overview:
        if active_plan:
            render_plan_visual(active_plan, pillars, rules)
        else:
            st.warning("No active plan. Activate a plan or build a new one with AI.")
            if plans:
                st.caption("Go to the AI builder tab or activate a plan from manual options below.")
                _render_plan_list(client, token, company_id, can_edit, plans, None)

    with tab_pillars:
        _render_pillars_tab(client, token, company_id, can_edit, pillars, active_plan)

    with tab_schedule:
        _render_rules_tab(client, token, company_id, can_edit, rules)


def _render_get_started(client: ApiClient, token: str, company_id: int, can_edit: bool) -> None:
    st.markdown("### Get started")
    st.caption(
        "Enter keywords and/or describe your expectations. AI will draft goals, content pillars, "
        "and a weekly posting schedule using your company profile and knowledge base."
    )
    if can_edit:
        _render_ai_builder(client, token, company_id, can_edit, expanded=True)
        st.divider()
        _render_manual_options(client, token, company_id, expanded=True)
    else:
        st.info("You have read-only access.")


def _render_ai_builder(
    client: ApiClient,
    token: str,
    company_id: int,
    can_edit: bool,
    expanded: bool = True,
) -> None:
    if not can_edit:
        st.info("You have read-only access.")
        return

    container = st.container(border=True)
    with container:
        st.markdown("#### Build with AI")
        st.caption("Powered by your company profile, brand voice, knowledge base, and the marketing_plan prompt.")

        with st.form("ai_plan_form"):
            plan_expectations = st.text_area(
                "Plan expectations & direction",
                placeholder=(
                    "e.g. KJSolutions marketing plan will help a fresh start-up market their new "
                    "platform selling social media automatic post generation SaaS."
                ),
                height=120,
                help="Describe your goals, context, and strategic direction for this plan.",
            )
            keywords = st.text_area(
                "Keywords & themes (optional)",
                placeholder="e.g. B2B SaaS, product launches, thought leadership, customer success",
                height=80,
            )
            focus_areas = st.text_input(
                "Focus areas (optional)",
                placeholder="e.g. lead generation, employer branding",
            )
            platforms = st.multiselect(
                "Platforms",
                PLATFORM_OPTIONS,
                default=["linkedin"],
                format_func=lambda p: p.title(),
            )
            col1, col2, col3 = st.columns(3)
            with col1:
                plan_name = st.text_input("Plan name (optional)", placeholder="AI will suggest if empty")
            with col2:
                period_weeks = st.number_input("Planning horizon (weeks)", min_value=1, max_value=52, value=12)
            with col3:
                posts_per_week = st.number_input("Posts per week", min_value=1, max_value=21, value=3)
            st.caption(
                "Posting times are set using platform engagement research (e.g. LinkedIn peak: "
                "Tue–Thu mornings). Regenerate to refresh an existing schedule."
            )
            replace = st.checkbox(
                "Replace existing pillars & schedule",
                value=True,
                help="When checked, regenerating clears current pillars and posting rules.",
            )
            submitted = st.form_submit_button("Generate marketing plan", type="primary", use_container_width=True)

        if submitted:
            if not plan_expectations.strip() and not keywords.strip():
                st.error("Provide plan expectations or keywords/themes.")
            elif not platforms:
                st.error("Select at least one platform.")
            else:
                with st.spinner("Designing your marketing plan with AI…"):
                    try:
                        result = client.generate_marketing_plan(
                            token,
                            company_id,
                            {
                                "plan_expectations": plan_expectations.strip() or None,
                                "keywords": keywords.strip(),
                                "focus_areas": focus_areas.strip() or None,
                                "platforms": platforms,
                                "plan_name": plan_name.strip() or None,
                                "period_weeks": int(period_weeks),
                                "posts_per_week": int(posts_per_week),
                                "replace_existing": replace,
                            },
                        )
                        st.success(
                            f"Created **{result['plan']['name']}** with "
                            f"{len(result['pillars'])} pillars and "
                            f"{len(result['posting_rules'])} posting rules."
                        )
                        st.rerun()
                    except ApiError as exc:
                        st.error(str(exc))


def _render_manual_options(
    client: ApiClient,
    token: str,
    company_id: int,
    expanded: bool,
) -> None:
    label = "Manual create or upload"
    section = st.expander(label, expanded=expanded) if not expanded else st.container()
    with section:
        col_create, col_upload = st.columns(2)
        with col_create:
            st.markdown("##### Create manually")
            with st.form("manual_plan_form"):
                name = st.text_input("Plan name", key="manual_plan_name")
                goals = st.text_area("Goals", key="manual_plan_goals", height=100)
                create = st.form_submit_button("Create & activate")
            if create and name.strip():
                try:
                    plan = client.create_marketing_plan(
                        token, company_id, {"name": name.strip(), "goals": goals.strip() or None}
                    )
                    client.update_marketing_plan(token, company_id, plan["id"], {"status": "active"})
                    st.success("Plan created.")
                    st.rerun()
                except ApiError as exc:
                    st.error(str(exc))
        with col_upload:
            st.markdown("##### Upload document")
            st.caption(
                "Upload a marketing plan (.txt, .md, .csv, or .pdf). "
                "AI will extract goals, pillars, and posting schedule."
            )
            with st.form("manual_plan_upload_form", clear_on_submit=True):
                uploaded = st.file_uploader(
                    "Plan file",
                    key="manual_plan_upload",
                    help="PDF must contain selectable text (not scanned images).",
                )
                upload_name = st.text_input(
                    "Plan name (optional)",
                    placeholder="Defaults to name from document",
                    key="manual_upload_name",
                )
                replace_existing = st.checkbox("Replace existing pillars & schedule", value=True)
                submitted = st.form_submit_button("Upload & activate", type="primary")
            if submitted:
                if uploaded is None:
                    st.error("Choose a file to upload.")
                else:
                    ext = uploaded.name.rsplit(".", 1)[-1].lower() if "." in uploaded.name else ""
                    if ext not in PLAN_UPLOAD_EXTENSIONS:
                        st.error(f"Unsupported file type. Use: {', '.join(PLAN_UPLOAD_EXTENSIONS)}")
                    else:
                        with st.spinner("Extracting and structuring your plan…"):
                            try:
                                result = client.import_marketing_plan(
                                    token,
                                    company_id,
                                    uploaded.getvalue(),
                                    uploaded.name,
                                    uploaded.type or "application/octet-stream",
                                    plan_name=upload_name.strip() or None,
                                    replace_existing=replace_existing,
                                )
                                st.success(
                                    f"Imported **{result['plan']['name']}** with "
                                    f"{len(result['pillars'])} pillars and "
                                    f"{len(result['posting_rules'])} posting rules."
                                )
                                st.rerun()
                            except ApiError as exc:
                                st.error(str(exc))


def _render_plan_list(
    client: ApiClient,
    token: str,
    company_id: int,
    can_edit: bool,
    plans: list[dict],
    active_plan: dict | None,
) -> None:
    for plan in plans:
        with st.expander(f"{plan['name']} · {plan['status']}", expanded=False):
            if plan.get("goals"):
                st.markdown(plan["goals"])
            if can_edit and plan.get("status") != "active":
                if st.button("Set as active", key=f"activate_{plan['id']}"):
                    try:
                        client.update_marketing_plan(token, company_id, plan["id"], {"status": "active"})
                        st.rerun()
                    except ApiError as exc:
                        st.error(str(exc))


def _render_pillars_tab(
    client: ApiClient,
    token: str,
    company_id: int,
    can_edit: bool,
    pillars: list[dict],
    active_plan: dict | None,
) -> None:
    if not active_plan:
        st.info("Create or activate a plan first.")
        return

    if can_edit:
        with st.expander("Add pillar", expanded=not pillars):
            with st.form("add_pillar_form"):
                name = st.text_input("Pillar name")
                description = st.text_area("Description", height=80)
                weight = st.slider("Weight", 1, 10, 5)
                if st.form_submit_button("Add pillar", type="primary") and name.strip():
                    try:
                        client.create_content_pillar(
                            token,
                            company_id,
                            {
                                "name": name.strip(),
                                "description": description.strip() or None,
                                "weight": weight,
                                "marketing_plan_id": active_plan["id"],
                            },
                        )
                        st.rerun()
                    except ApiError as exc:
                        st.error(str(exc))

    if not pillars:
        st.caption("No pillars yet — use AI builder or add manually.")
        return

    for pillar in pillars:
        with st.container(border=True):
            st.markdown(f"**{pillar['name']}**")
            st.progress(pillar.get("weight", 5) / 10.0)
            if pillar.get("description"):
                st.caption(pillar["description"])
            if can_edit and st.button("Delete", key=f"del_pillar_{pillar['id']}"):
                try:
                    client.delete_content_pillar(token, company_id, pillar["id"])
                    st.rerun()
                except ApiError as exc:
                    st.error(str(exc))


def _render_rules_tab(
    client: ApiClient,
    token: str,
    company_id: int,
    can_edit: bool,
    rules: list[dict],
) -> None:
    if can_edit:
        with st.expander("Add posting rule", expanded=not rules):
            with st.form("add_rule_form"):
                c1, c2 = st.columns(2)
                with c1:
                    platform = st.selectbox("Platform", PLATFORM_OPTIONS)
                    post_type = st.selectbox("Post type", ["professional", "personal"])
                with c2:
                    weekday = st.selectbox("Weekday", range(7), format_func=lambda i: WEEKDAYS_FULL[i])
                    post_time = st.text_input("Time", value="09:00")
                frequency = st.selectbox("Frequency", ["weekly", "biweekly", "daily", "monthly"])
                if st.form_submit_button("Add rule", type="primary"):
                    try:
                        client.create_posting_rule(
                            token,
                            company_id,
                            {
                                "platform": platform,
                                "weekday": weekday,
                                "post_time": post_time,
                                "post_type": post_type,
                                "frequency": frequency,
                                "is_active": True,
                            },
                        )
                        st.rerun()
                    except ApiError as exc:
                        st.error(str(exc))

    if not rules:
        st.caption("No rules yet — use AI builder or add manually.")
        return

    rows = [
        {
            "Platform": r["platform"].title(),
            "Day": WEEKDAYS_FULL[r["weekday"]],
            "Time": r["post_time"],
            "Type": r["post_type"],
            "Frequency": r["frequency"],
            "Active": r.get("is_active", True),
        }
        for r in rules
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)

    for rule in rules:
        with st.expander(
            f"{rule['platform'].title()} · {WEEKDAYS_FULL[rule['weekday']]} {rule['post_time']}",
            expanded=False,
        ):
            if can_edit:
                c1, c2 = st.columns(2)
                with c1:
                    label = "Deactivate" if rule.get("is_active") else "Activate"
                    if st.button(label, key=f"toggle_{rule['id']}"):
                        try:
                            client.update_posting_rule(
                                token, company_id, rule["id"],
                                {"is_active": not rule.get("is_active")},
                            )
                            st.rerun()
                        except ApiError as exc:
                            st.error(str(exc))
                with c2:
                    if st.button("Delete", key=f"del_rule_{rule['id']}"):
                        try:
                            client.delete_posting_rule(token, company_id, rule["id"])
                            st.rerun()
                        except ApiError as exc:
                            st.error(str(exc))
