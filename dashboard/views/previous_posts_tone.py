import streamlit as st

from api_client import ApiClient, ApiError

PREVIOUS_POST_SOURCE = "previous_post"
UPLOAD_EXTENSIONS = ("txt", "md", "csv", "pdf", "doc", "docx")


def render_previous_posts_tone(
    client: ApiClient,
    token: str,
    company_id: int,
    can_edit: bool,
    *,
    key_prefix: str,
) -> None:
    st.subheader("Previous posts for tone")
    st.caption(
        "Add past posts so the AI learns your voice. Paste text or upload a document "
        "with examples from LinkedIn, Facebook, or other channels."
    )

    try:
        entries = client.list_knowledge(token, company_id)
    except ApiError as exc:
        st.error(str(exc))
        return

    tone_entries = [entry for entry in entries if entry.get("source") == PREVIOUS_POST_SOURCE]

    if can_edit:
        tab_paste, tab_upload = st.tabs(["Paste posts", "Upload document"])

        with tab_paste:
            with st.form(f"{key_prefix}_previous_posts_form"):
                title = st.text_input(
                    "Label",
                    placeholder="e.g. LinkedIn posts Q1 2026",
                    key=f"{key_prefix}_previous_posts_title",
                )
                content = st.text_area(
                    "Post examples",
                    height=180,
                    placeholder="Paste one or more previous posts here…",
                    key=f"{key_prefix}_previous_posts_content",
                )
                submitted = st.form_submit_button("Save examples", type="primary")
            if submitted:
                if not title.strip() or not content.strip():
                    st.error("Label and post examples are required.")
                else:
                    try:
                        client.add_knowledge(
                            token,
                            company_id,
                            {
                                "title": title.strip(),
                                "content": content.strip(),
                                "source": PREVIOUS_POST_SOURCE,
                            },
                        )
                        st.success("Previous posts saved.")
                        st.rerun()
                    except ApiError as exc:
                        st.error(str(exc))

        with tab_upload:
            uploaded = st.file_uploader(
                "Upload document with past posts",
                type=list(UPLOAD_EXTENSIONS),
                key=f"{key_prefix}_previous_posts_upload",
            )
            if uploaded and st.button("Upload examples", key=f"{key_prefix}_previous_posts_upload_btn"):
                try:
                    client.upload_file(
                        token,
                        company_id,
                        uploaded.getvalue(),
                        uploaded.name,
                        uploaded.type or "application/octet-stream",
                        kind="knowledge",
                        knowledge_source=PREVIOUS_POST_SOURCE,
                    )
                    st.success("Document uploaded and indexed for tone.")
                    st.rerun()
                except ApiError as exc:
                    st.error(str(exc))

    if not tone_entries:
        st.info("No previous posts added yet.")
        return

    st.markdown(f"**Saved examples ({len(tone_entries)})**")
    for entry in tone_entries:
        with st.expander(entry["title"], expanded=False):
            st.caption(entry["created_at"][:19].replace("T", " "))
            preview = entry["content"]
            st.markdown(preview[:4000] + ("…" if len(preview) > 4000 else ""))
            if can_edit:
                if st.button("Delete", key=f"del_tone_{key_prefix}_{entry['id']}"):
                    try:
                        client.delete_knowledge(token, company_id, entry["id"])
                        st.success("Deleted.")
                        st.rerun()
                    except ApiError as exc:
                        st.error(str(exc))
