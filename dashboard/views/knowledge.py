import streamlit as st

from api_client import ApiClient, ApiError


def render_knowledge_base(client: ApiClient, token: str, company_id: int, can_edit: bool) -> None:
    st.caption(
        "Add business context used when generating posts. Text files (.txt, .md, .csv) are indexed automatically on upload."
    )

    try:
        entries = client.list_knowledge(token, company_id)
    except ApiError as exc:
        st.error(str(exc))
        return

    if can_edit:
        tab_add, tab_upload = st.tabs(["Add text", "Upload document"])

        with tab_add:
            with st.form("knowledge_form"):
                title = st.text_input("Title", placeholder="e.g. Product overview, Q1 goals")
                content = st.text_area("Content", height=200, placeholder="Facts, messaging, FAQs…")
                submitted = st.form_submit_button("Save to knowledge base", type="primary")
            if submitted:
                if not title.strip() or not content.strip():
                    st.error("Title and content are required.")
                else:
                    try:
                        client.add_knowledge(
                            token,
                            company_id,
                            {"title": title.strip(), "content": content.strip()},
                        )
                        st.success("Knowledge entry saved.")
                        st.rerun()
                    except ApiError as exc:
                        st.error(str(exc))

        with tab_upload:
            uploaded = st.file_uploader(
                "Upload document",
                type=["txt", "md", "csv", "pdf", "doc", "docx"],
                key="knowledge_upload",
            )
            if uploaded and st.button("Upload and index", key="knowledge_upload_btn"):
                try:
                    client.upload_file(
                        token,
                        company_id,
                        uploaded.getvalue(),
                        uploaded.name,
                        uploaded.type or "application/octet-stream",
                        kind="knowledge",
                    )
                    st.success("File uploaded. Text files are indexed automatically.")
                    st.rerun()
                except ApiError as exc:
                    st.error(str(exc))

    st.subheader(f"Entries ({len(entries)})")
    if not entries:
        st.info("No knowledge entries yet. Add text or upload a document to improve post generation.")
        return

    for entry in entries:
        with st.expander(f"{entry['title']} · {entry['source']}", expanded=False):
            st.caption(entry["created_at"][:19].replace("T", " "))
            st.markdown(entry["content"][:5000] + ("…" if len(entry["content"]) > 5000 else ""))
            if can_edit:
                if st.button("Delete", key=f"del_kb_{entry['id']}"):
                    try:
                        client.delete_knowledge(token, company_id, entry["id"])
                        st.success("Deleted.")
                        st.rerun()
                    except ApiError as exc:
                        st.error(str(exc))
