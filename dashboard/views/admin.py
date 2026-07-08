import streamlit as st

from api_client import ApiClient, ApiError
from components.layout import page_header


def render_admin_dashboard(client: ApiClient, token: str) -> None:
    page_header("Admin Dashboard", "Platform-wide overview for developers and operators.")

    tab_overview, tab_companies, tab_usage, tab_prompts, tab_jobs, tab_users = st.tabs(
        ["Overview", "Companies", "Usage", "Prompts", "Publishing jobs", "Users"]
    )

    try:
        usage = client.admin_usage(token)
        companies = client.admin_companies(token)
        prompts = client.admin_prompts(token)
        jobs = client.admin_jobs(token)
        users = client.admin_users(token)
    except ApiError as exc:
        if exc.status_code == 403:
            st.error("Platform admin access required. Set PLATFORM_ADMIN_EMAIL in backend/.env and restart the API.")
        else:
            st.error(str(exc))
        return

    with tab_overview:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Companies", len(companies))
        col2.metric("Users", len(users))
        col3.metric("Total tokens", f"{usage['total_tokens']:,}")
        col4.metric("Est. cost (USD)", f"${usage['total_cost_usd']:.4f}")
        st.write(f"**OpenAI API calls logged:** {usage['total_events']}")
        st.write(f"**Publishing jobs:** {len(jobs)}")

    with tab_companies:
        if not companies:
            st.info("No companies yet.")
        else:
            st.dataframe(
                [
                    {
                        "ID": c["id"],
                        "Name": c["name"],
                        "Slug": c["slug"],
                        "Members": c["member_count"],
                        "Posts": c["post_count"],
                        "Tokens": c["total_tokens"],
                        "Cost USD": round(c["total_cost_usd"], 4),
                    }
                    for c in companies
                ],
                use_container_width=True,
                hide_index=True,
            )

    with tab_usage:
        st.metric("Total estimated cost", f"${usage['total_cost_usd']:.4f}")
        st.metric("Total tokens", f"{usage['total_tokens']:,}")
        st.subheader("Usage by company")
        st.dataframe(
            [
                {
                    "Company": c["name"],
                    "Tokens": c["total_tokens"],
                    "Cost USD": round(c["total_cost_usd"], 4),
                    "Posts generated": c["post_count"],
                }
                for c in sorted(companies, key=lambda x: x["total_cost_usd"], reverse=True)
            ],
            use_container_width=True,
            hide_index=True,
        )

    with tab_prompts:
        for prompt in prompts:
            with st.expander(f"{prompt['key']} (v{prompt.get('active_version', '?')})"):
                st.write(f"**Kind:** {prompt['kind']}")
                if prompt.get("description"):
                    st.write(prompt["description"])
                if prompt.get("body_preview"):
                    st.code(prompt["body_preview"])

    with tab_jobs:
        if not jobs:
            st.info("No publishing jobs yet.")
        else:
            st.dataframe(
                [
                    {
                        "ID": j["id"],
                        "Company": j["company_name"],
                        "Platform": j.get("platform"),
                        "Status": j["status"],
                        "Hook": (j.get("hook_preview") or "")[:60],
                        "Mock post ID": j.get("external_post_id"),
                    }
                    for j in jobs
                ],
                use_container_width=True,
                hide_index=True,
            )

    with tab_users:
        st.dataframe(
            [
                {
                    "ID": u["id"],
                    "Email": u["email"],
                    "Admin": u["is_platform_admin"],
                    "Companies": u["company_count"],
                }
                for u in users
            ],
            use_container_width=True,
            hide_index=True,
        )
