import streamlit as st

from api_client import ApiClient, ApiError
from components.layout import page_header
from views.knowledge import render_knowledge_base


def render_company_profile(client: ApiClient, token: str, company_id: int, can_edit: bool) -> None:
    page_header("Company Profile", "Business context and knowledge base for AI generation.")

    tab_details, tab_knowledge = st.tabs(["Company details", "Knowledge base"])

    with tab_details:
        st.caption("Business information used as context for AI post generation.")

        try:
            profile = client.get_company_profile(token, company_id)
        except ApiError as exc:
            st.error(str(exc))
            return

        if not can_edit:
            st.info("You have read-only access to this company.")

        with st.form("company_profile_form"):
            legal_name = st.text_input("Legal name", value=profile.get("legal_name") or "")
            industry = st.text_input("Industry", value=profile.get("industry") or "")
            website = st.text_input("Website", value=profile.get("website") or "")
            location = st.text_input("Location", value=profile.get("location") or "")
            description = st.text_area("About the company", value=profile.get("description") or "")
            target_audience = st.text_area(
                "Target audience", value=profile.get("target_audience") or ""
            )
            products_services = st.text_area(
                "Products & services", value=profile.get("products_services") or ""
            )
            submitted = st.form_submit_button("Save company profile", disabled=not can_edit)

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

    with tab_knowledge:
        render_knowledge_base(client, token, company_id, can_edit)