import streamlit as st

from api_client import ApiClient, ApiError
from components.layout import page_header
from components.platform_preview import render_platform_preview
from components.post_image import load_post_image


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
    page_header("Publishing Queue", "Publish queued posts to your connected social accounts.")

    try:
        queue = client.list_publishing_queue(token, company_id)
        accounts = client.list_connected_accounts(token, company_id)
    except ApiError as exc:
        st.error(str(exc))
        return

    has_real = any(not a.get("is_mock") and a.get("status") == "active" for a in accounts)
    if not has_real and can_edit:
        st.info("Connect LinkedIn or Facebook in the **Connections** tab before publishing for real.")

    st.subheader(f"Queued posts ({len(queue)})")

    if not queue:
        st.success("No posts waiting in the queue.")
    else:
        publish_label = "Publish all queued" if has_real else "Publish all queued (mock)"
        if can_edit and st.button(publish_label, type="primary"):
            with st.spinner("Publishing…"):
                try:
                    results = client.publish_all(token, company_id)
                    st.success(f"Published {len(results)} post(s).")
                    st.rerun()
                except ApiError as exc:
                    st.error(str(exc))

        for item in queue:
            with st.expander(
                f"{item['platform']} · {item.get('hook_preview') or 'Untitled'}",
                expanded=True,
            ):
                st.caption(_schedule_caption(item))
                st.subheader("Feed preview")
                _render_feed_preview(client, token, company_id, company_name, item)
                if can_edit:
                    single_label = "Publish now" if has_real else "Publish now (mock)"
                    if st.button(single_label, key=f"publish_{item['id']}"):
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
    page_header("Previous Posts", "Posts that have been published and delivered.")

    try:
        jobs = client.list_publishing_jobs(token, company_id)
    except ApiError as exc:
        st.error(str(exc))
        return

    published = [j for j in jobs if j.get("status") == "completed"]

    if not published:
        st.info("No posts have been published yet. Publish a queued post to see it here.")
        return

    st.subheader(f"Published posts ({len(published)})")
    for job in published:
        label = f"{str(job.get('platform') or 'unknown').title()} · {job.get('hook_preview') or 'Post'}"
        with st.expander(label, expanded=False):
            published_at = job.get("completed_at") or job.get("created_at")
            if published_at:
                st.caption(f"Published {published_at[:19].replace('T', ' ')}")
            if job.get("external_post_id"):
                st.caption(f"Post ID: `{job['external_post_id']}`")
            if job.get("content"):
                st.subheader("Feed preview")
                _render_feed_preview(client, token, company_id, company_name, job)
