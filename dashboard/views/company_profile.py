import streamlit as st

from api_client import ApiClient, ApiError
from components.layout import page_header
from views.knowledge import render_knowledge_base
from views.previous_posts_tone import render_previous_posts_tone


def _profile_has_data(profile: dict) -> bool:
    fields = [
        profile.get("legal_name"),
        profile.get("industry"),
        profile.get("description"),
        profile.get("target_audience"),
        profile.get("products_services"),
    ]
    return any(field and str(field).strip() for field in fields)


def render_company_profile(client: ApiClient, token: str, company_id: int, can_edit: bool) -> None:
    page_header(
        "Company Profile",
        "Paste your company website URL to auto-fill, then review and edit.",
    )

    tab_details, tab_knowledge = st.tabs(["Company details", "Knowledge base"])

    with tab_details:
        try:
            profile = client.get_company_profile(token, company_id)
        except ApiError as exc:
            st.error(str(exc))
            return

        if not can_edit:
            st.info("You have read-only access to this company.")

        tab_import, tab_manual = st.tabs(["Import from website", "Fill manually"])

        with tab_import:
            st.caption(
                "We fetch your public homepage or about page, extract business context with AI, "
                "and save it to your profile. Review and edit anything in the **Fill manually** tab."
            )

            default_url = profile.get("website") or ""
            url = st.text_input(
                "Company website URL",
                value=default_url,
                placeholder="https://example.com",
                disabled=not can_edit,
            )

            if st.button(
                "Import from website",
                type="primary",
                disabled=not can_edit,
                use_container_width=True,
            ):
                if not url.strip():
                    st.error("Enter a company website URL.")
                else:
                    with st.spinner("Fetching website and building your company profile…"):
                        try:
                            client.scrape_company_profile_from_url(
                                token, company_id, url.strip()
                            )
                            st.success(
                                "Profile imported from your website. "
                                "Open **Fill manually** to review and edit."
                            )
                            st.rerun()
                        except ApiError as exc:
                            st.error(str(exc))

            if not _profile_has_data(profile):
                st.info(
                    "New here? Paste your company URL above for the fastest setup. "
                    "You can always fill fields manually instead."
                )

        with tab_manual:
            st.caption("Business information used as context for AI post generation.")

            with st.form("company_profile_form"):
                legal_name = st.text_input("Legal name", value=profile.get("legal_name") or "")
                industry = st.text_input("Industry", value=profile.get("industry") or "")
                website = st.text_input("Website", value=profile.get("website") or "")
                location = st.text_input("Location", value=profile.get("location") or "")
                description = st.text_area(
                    "About the company", value=profile.get("description") or ""
                )
                target_audience = st.text_area(
                    "Target audience", value=profile.get("target_audience") or ""
                )
                products_services = st.text_area(
                    "Products & services", value=profile.get("products_services") or ""
                )
                submitted = st.form_submit_button(
                    "Save company profile", disabled=not can_edit, use_container_width=True
                )

            if submitted:
                payload = {
                    "legal_name": legal_name.strip() or None,
                    "industry": industry.strip() or None,
                    "website": website.strip() or None,
                    "location": location.strip() or None,
                    "description": description.strip() or None,
                    "target_audience": target_audience.strip() or None,
                    "products_services": products_services.strip() or None,
                }
                try:
                    client.update_company_profile(token, company_id, payload)
                    st.success("Company profile saved.")
                    st.rerun()
                except ApiError as exc:
                    st.error(str(exc))

        st.divider()
        render_previous_posts_tone(client, token, company_id, can_edit, key_prefix="company")

    with tab_knowledge:
        render_knowledge_base(client, token, company_id, can_edit)
