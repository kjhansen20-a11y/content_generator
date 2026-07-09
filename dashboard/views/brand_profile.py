import streamlit as st

from api_client import ApiClient, ApiError
from components.layout import page_header
from views.previous_posts_tone import render_previous_posts_tone


def render_brand_profile(client: ApiClient, token: str, company_id: int, can_edit: bool) -> None:
    page_header("Brand Profile", "Voice, tone, and brand rules used when generating posts.")

    try:
        profile = client.get_brand_profile(token, company_id)
    except ApiError as exc:
        st.error(str(exc))
        return

    if not can_edit:
        st.info("You have read-only access to this company.")

    with st.form("brand_profile_form"):
        tone_of_voice = st.text_input(
            "Tone of voice (short label)",
            value=profile.get("tone_of_voice") or "",
            placeholder="e.g. Professional, approachable, expert",
        )
        brand_voice_description = st.text_area(
            "Brand voice description",
            value=profile.get("brand_voice_description") or "",
            placeholder="How should posts sound? Formal or casual? First person or we?",
        )
        do_use = st.text_area(
            "Do use (topics, phrases, angles)",
            value=profile.get("do_use") or "",
            placeholder="Topics, phrases, or angles to emphasize",
        )
        dont_use = st.text_area(
            "Don't use",
            value=profile.get("dont_use") or "",
            placeholder="Words, claims, or topics to avoid",
        )
        brand_keywords = st.text_area(
            "Brand keywords",
            value=profile.get("brand_keywords") or "",
            placeholder="Comma-separated keywords associated with your brand",
        )
        submitted = st.form_submit_button("Save brand profile", disabled=not can_edit)

    if submitted:
        payload = {
            "tone_of_voice": tone_of_voice.strip() or None,
            "brand_voice_description": brand_voice_description.strip() or None,
            "do_use": do_use.strip() or None,
            "dont_use": dont_use.strip() or None,
            "brand_keywords": brand_keywords.strip() or None,
        }
        try:
            client.update_brand_profile(token, company_id, payload)
            st.success("Brand profile saved.")
            st.rerun()
        except ApiError as exc:
            st.error(str(exc))

    st.divider()
    render_previous_posts_tone(client, token, company_id, can_edit, key_prefix="brand")
