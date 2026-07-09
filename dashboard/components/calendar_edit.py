from datetime import date, time

import streamlit as st

from api_client import ApiClient, ApiError


def _parse_time(value: str | None) -> time | None:
    if not value:
        return None
    try:
        hh, mm = value.split(":")[:2]
        return time(int(hh), int(mm))
    except (ValueError, TypeError):
        return None


def render_calendar_edit_form(
    client: ApiClient,
    token: str,
    company_id: int,
    item: dict,
    *,
    key_prefix: str = "edit",
    success_message: str = "Post saved.",
) -> None:
    content = item["content"]
    scheduled = item.get("scheduled_date")
    default_date = date.fromisoformat(scheduled) if scheduled else date.today()
    default_time = _parse_time(item.get("scheduled_time")) or time(9, 0)
    from_plan = bool(item.get("posting_rule_id"))
    item_id = item["id"]

    sched_key = f"{key_prefix}_use_schedule_{item_id}"
    if sched_key not in st.session_state:
        st.session_state[sched_key] = bool(scheduled)
    if from_plan:
        st.caption("This post is tied to a marketing plan slot. Date and time are from your plan.")
    use_schedule = st.checkbox("Set scheduled date", key=sched_key, disabled=from_plan)
    scheduled_date = default_date
    scheduled_time = default_time
    if use_schedule or from_plan:
        sched_col1, sched_col2 = st.columns(2)
        scheduled_date = sched_col1.date_input(
            "Scheduled date",
            value=default_date,
            key=f"{key_prefix}_sched_date_{item_id}",
            disabled=from_plan,
        )
        scheduled_time = sched_col2.time_input(
            "Scheduled time",
            value=default_time,
            key=f"{key_prefix}_sched_time_{item_id}",
            disabled=from_plan,
        )

    with st.form(f"{key_prefix}_form_{item_id}"):
        hook = st.text_input("Hook", value=content.get("hook", ""))
        body = st.text_area("Body", value=content.get("body", ""), height=200)
        hashtags_text = st.text_input(
            "Hashtags (comma-separated)",
            value=", ".join(content.get("hashtags") or []),
        )
        alt_text = st.text_input("Alt text", value=content.get("alt_text") or "")
        suggested_time = st.text_input(
            "Suggested publish time",
            value=content.get("suggested_publish_time") or "",
        )
        save = st.form_submit_button("Save changes", type="primary")

    if save:
        if not hook.strip() or not body.strip():
            st.error("Hook and body are required.")
            return
        hashtags = [h.strip().lstrip("#") for h in hashtags_text.split(",") if h.strip()]
        payload = {
            "hook": hook.strip(),
            "body": body.strip(),
            "hashtags": hashtags,
            "alt_text": alt_text.strip() or None,
            "suggested_publish_time": suggested_time.strip() or None,
            "scheduled_date": scheduled_date.isoformat() if (use_schedule or from_plan) else None,
            "scheduled_time": scheduled_time.strftime("%H:%M") if (use_schedule or from_plan) else None,
        }
        try:
            client.update_calendar_item(token, company_id, item_id, payload)
            st.success(success_message)
            st.rerun()
        except ApiError as exc:
            st.error(str(exc))
