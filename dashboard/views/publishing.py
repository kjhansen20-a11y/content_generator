import streamlit as st

from api_client import ApiClient, ApiError
from components.calendar_edit import render_calendar_edit_form
from components.layout import page_header, section_title
from components.platform_preview import render_platform_preview
from components.post_image import load_post_image

PLATFORM_LABELS = {"linkedin": "LinkedIn", "facebook": "Facebook"}


POST_TYPE_LABELS = {
    "professional": "Professional → Company Page",
    "personal": "Personal → Your profile",
}


def _item_publish_ready(accounts: list[dict], item: dict) -> bool:
    platform = item.get("platform", "")
    if platform == "facebook":
        return _platform_connected(accounts, "facebook")
    if platform == "linkedin":
        post_type = item.get("post_type", "professional")
        account_type = "profile" if post_type == "personal" else "organization"
        return any(
            a.get("platform") == "linkedin"
            and not a.get("is_mock")
            and a.get("status") == "active"
            and a.get("account_type") == account_type
            for a in accounts
        )
    return False


def _publish_target_label(item: dict) -> str:
    platform = PLATFORM_LABELS.get(item.get("platform", ""), item.get("platform", "").title())
    post_type = item.get("post_type", "professional")
    if item.get("platform") == "linkedin":
        if post_type == "personal":
            return f"{platform} · Personal profile"
        return f"{platform} · Company Page"
    return platform


def _platform_connected(accounts: list[dict], platform: str) -> bool:
    return any(
        a.get("platform") == platform and not a.get("is_mock") and a.get("status") == "active"
        for a in accounts
    )


def _render_feed_preview(
    client: ApiClient,
    token: str,
    company_id: int,
    company_name: str,
    item: dict,
) -> None:
    platform = item.get("platform", "linkedin")
    content = item.get("content")
    if not content:
        return
    img_b64, img_mime = load_post_image(client, token, company_id, item.get("image_file_id"))
    render_platform_preview(
        platform,
        company_name,
        content,
        image_base64=img_b64,
        image_mime=img_mime,
    )


def render_publishing_queue(
    client: ApiClient,
    token: str,
    company_id: int,
    can_edit: bool,
    company_name: str = "Your Company",
) -> None:
    page_header(
        "Publishing Queue",
        "Each queued post publishes to the platform set when you created it (LinkedIn or Facebook).",
        eyebrow="Publishing",
    )

    try:
        queue = client.list_publishing_queue(token, company_id)
        accounts = client.list_connected_accounts(token, company_id)
    except ApiError as exc:
        st.error(str(exc))
        return

    if not queue:
        st.success("No posts waiting in the queue.")
        return

    ready_count = sum(1 for item in queue if _item_publish_ready(accounts, item))
    section_title(f"Queued posts ({len(queue)})")
    if ready_count < len(queue):
        st.warning(
            "Some queued posts are missing a connected account for their target platform. "
            "Connect the matching platform in **Connections** before publishing."
        )

    if can_edit and st.button("Publish all queued", type="primary"):
        with st.spinner("Publishing…"):
            try:
                results = client.publish_all(token, company_id)
                st.success(f"Published {len(results)} post(s).")
                st.rerun()
            except ApiError as exc:
                st.error(str(exc))

    for item in queue:
        platform = item.get("platform", "linkedin")
        platform_label = PLATFORM_LABELS.get(platform, platform.title())
        target_label = _publish_target_label(item)
        with st.expander(
            f"{target_label} · {item.get('hook_preview') or 'Untitled'}",
            expanded=True,
        ):
            st.markdown(f"**Publish to:** {target_label}")
            st.caption(POST_TYPE_LABELS.get(item.get("post_type", "professional"), ""))
            st.caption(_schedule_caption(item))
            if not _item_publish_ready(accounts, item):
                if platform == "linkedin" and item.get("post_type") == "personal":
                    st.error("Connect your **LinkedIn personal profile** in Connections.")
                elif platform == "linkedin":
                    st.error(
                        "Connect your **LinkedIn Company Page** in Connections "
                        "(requires Community Management API on your LinkedIn app)."
                    )
                else:
                    st.error(f"Connect **{platform_label}** in Connections to publish this post.")
            elif item.get("image_file_id") and not load_post_image(
                client, token, company_id, item.get("image_file_id")
            )[0]:
                st.warning(
                    "Image file is missing on the server. You can still publish as text-only, "
                    "or delete this post and generate a new one with an image."
                )
            st.subheader("Feed preview")
            _render_feed_preview(client, token, company_id, company_name, item)

            if can_edit and st.session_state.get(f"edit_queue_{item['id']}"):
                st.divider()
                render_calendar_edit_form(
                    client,
                    token,
                    company_id,
                    item,
                    key_prefix=f"queue_{item['id']}",
                    success_message="Queued post updated.",
                )
                if st.button("Done editing", key=f"done_edit_queue_{item['id']}"):
                    st.session_state.pop(f"edit_queue_{item['id']}", None)
                    st.rerun()
                continue

            if can_edit:
                col_edit, col_delete, col_publish = st.columns(3)
                if col_edit.button("Edit", key=f"edit_queue_{item['id']}", use_container_width=True):
                    st.session_state[f"edit_queue_{item['id']}"] = True
                    st.rerun()
                if col_delete.button("Delete", key=f"delete_queue_{item['id']}", use_container_width=True):
                    try:
                        client.delete_calendar_item(token, company_id, item["id"])
                        st.success("Post removed from queue.")
                        st.rerun()
                    except ApiError as exc:
                        st.error(str(exc))
                if col_publish.button(
                    f"Publish to {target_label}",
                    key=f"publish_{item['id']}",
                    disabled=not _item_publish_ready(accounts, item),
                    use_container_width=True,
                ):
                    try:
                        result = client.publish_item(token, company_id, item["id"])
                        st.success(result["job"]["result_message"])
                        st.rerun()
                    except ApiError as exc:
                        st.error(str(exc))


def _schedule_caption(item: dict) -> str:
    if not item.get("scheduled_date"):
        return "Not scheduled"
    label = f"Scheduled {item['scheduled_date']}"
    if item.get("scheduled_time"):
        label += f" at {item['scheduled_time']}"
    return label


def render_previous_posts(
    client: ApiClient,
    token: str,
    company_id: int,
    company_name: str = "Your Company",
) -> None:
    page_header("Previous Posts", "Posts that have been published and delivered.", eyebrow="Publishing")

    try:
        jobs = client.list_publishing_jobs(token, company_id)
    except ApiError as exc:
        st.error(str(exc))
        return

    published = [j for j in jobs if j.get("status") == "completed"]

    if not published:
        st.info("No posts have been published yet. Publish a queued post to see it here.")
        return

    section_title(f"Published posts ({len(published)})")
    for job in published:
        platform = str(job.get("platform") or "unknown")
        platform_label = PLATFORM_LABELS.get(platform, platform.title())
        label = f"{platform_label} · {job.get('hook_preview') or 'Post'}"
        with st.expander(label, expanded=False):
            published_at = job.get("completed_at") or job.get("created_at")
            if published_at:
                st.caption(f"Published {published_at[:19].replace('T', ' ')}")
            if job.get("external_post_id"):
                st.caption(f"Post ID: `{job['external_post_id']}`")
            if job.get("content"):
                st.subheader("Feed preview")
                _render_feed_preview(client, token, company_id, company_name, job)
