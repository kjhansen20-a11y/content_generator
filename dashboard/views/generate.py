from datetime import date, time

import streamlit as st

from api_client import ApiClient, ApiError
from components.layout import page_header
from components.platform_preview import render_platform_preview
from components.post_image import load_post_image
from components.posting_time_guide import render_posting_time_guide

PUBLISH_PLATFORMS = ["linkedin", "facebook"]
PLATFORM_LABELS = {"linkedin": "LinkedIn", "facebook": "Facebook"}
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

GEN_MODE_LABELS = {
    "instant": "Instant post",
    "manual": "Schedule — pick date & time",
    "follow_plan": "Follow marketing plan",
}

POST_LANGUAGE_OPTIONS = {
    "auto": "Auto-detect",
    "da": "Danish",
    "en": "English",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "sv": "Swedish",
    "no": "Norwegian",
    "nl": "Dutch",
    "it": "Italian",
    "pt": "Portuguese",
    "pl": "Polish",
    "fi": "Finnish",
}

_GEN_FORM_KEYS = (
    "last_generated_id",
    "edit_generated",
    "last_slot_label",
    "last_schedule_label",
    "show_next_week_offer",
    "pending_next_week_generate",
    "gen_mode",
    "gen_sched_date",
    "gen_sched_time",
)


def _start_new_post() -> None:
    for key in _GEN_FORM_KEYS:
        st.session_state.pop(key, None)
    st.session_state["gen_reset_nonce"] = st.session_state.get("gen_reset_nonce", 0) + 1


def render_generate_post(client: ApiClient, token: str, company_id: int, can_edit: bool) -> None:
    page_header(
        "Generate Post",
        "Instant on-brand posts, manual scheduling, or follow your marketing plan slots.",
    )

    if not can_edit:
        st.info("You have read-only access. Generation requires editor permissions.")
        return

    if "gen_reset_nonce" not in st.session_state:
        st.session_state.gen_reset_nonce = 0
    form_nonce = st.session_state.gen_reset_nonce

    use_next_week = False
    trigger = False

    if st.session_state.pop("pending_next_week_generate", False):
        st.session_state["gen_mode"] = "follow_plan"
        use_next_week = True
        trigger = True

    gen_mode = st.radio(
        "Generation mode",
        options=["instant", "manual", "follow_plan"],
        format_func=lambda x: GEN_MODE_LABELS[x],
        horizontal=True,
        key="gen_mode",
    )

    if gen_mode == "instant" and _company_has_posting_rules(client, token, company_id):
        st.caption(
            "Tip: choose **Follow marketing plan** to use your planned platform, post type, date, and time."
        )

    post_type = "professional"
    platform = "linkedin"
    scheduled_date_value: date | None = None
    scheduled_time_value: time | None = None

    if gen_mode == "follow_plan":
        st.caption(
            "Platform, post type, date, and time come from the next open slot in your marketing plan."
        )
        has_rules = _render_follow_plan_context(client, token, company_id)
        if not has_rules:
            st.error("Add a marketing plan with posting rules before using this mode.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            post_type = st.selectbox(
                "Post type",
                options=["professional", "personal"],
                format_func=lambda x: (
                    "Professional / Educational → Company Page"
                    if x == "professional"
                    else "Personal / Founder → Your profile"
                ),
                help="For LinkedIn: professional posts publish to your Company Page; personal posts publish from your profile.",
                key=f"gen_post_type_{form_nonce}",
            )
        with col2:
            platform = st.selectbox(
                "Publish to",
                options=PUBLISH_PLATFORMS,
                format_func=lambda x: PLATFORM_LABELS[x],
                help="This post will be published to the platform you choose when you queue it.",
                key=f"gen_platform_{form_nonce}",
            )

        st.info(f"This post will publish to **{PLATFORM_LABELS[platform]}** when you queue and publish it.")

        if gen_mode == "manual":
            render_posting_time_guide(platform)
            sched_col1, sched_col2 = st.columns(2)
            scheduled_date_value = sched_col1.date_input(
                "Scheduled date", value=date.today(), key="gen_sched_date"
            )
            scheduled_time_value = sched_col2.time_input(
                "Scheduled time", value=time(9, 0), key="gen_sched_time"
            )

    output_language = st.selectbox(
        "Post language",
        options=list(POST_LANGUAGE_OPTIONS.keys()),
        format_func=lambda code: POST_LANGUAGE_OPTIONS[code],
        key=f"gen_output_language_{form_nonce}",
    )

    content_idea = st.text_area(
        "Content idea",
        placeholder="What should this post be about?",
        height=80,
        key=f"gen_content_idea_{form_nonce}",
    )
    keywords = st.text_input("Keywords (optional)", key=f"gen_keywords_{form_nonce}")
    uploaded_image = st.file_uploader(
        "Post image",
        type=["png", "jpg", "jpeg", "webp", "gif"],
        help="Upload the image to publish with this post.",
        key=f"gen_image_upload_{form_nonce}",
    )
    image_description = st.text_input(
        "Image description (optional)",
        placeholder="Describe the image for accessibility and AI context",
        key=f"gen_image_desc_{form_nonce}",
    )

    if not trigger:
        trigger = st.button("Generate draft", type="primary", key="generate_draft_btn")

    if trigger:
        gen_mode = st.session_state.get("gen_mode", gen_mode)
        if gen_mode == "follow_plan" and not _company_has_posting_rules(client, token, company_id):
            st.error("No active posting rules found. Create or regenerate your marketing plan first.")
        else:
            payload = _build_payload(
                gen_mode=gen_mode,
                post_type=post_type,
                platform=platform,
                content_idea=content_idea,
                keywords=keywords,
                image_description=image_description,
                output_language=output_language,
                scheduled_date_value=scheduled_date_value,
                scheduled_time_value=scheduled_time_value,
                use_next_week=use_next_week,
            )
            with st.spinner("Generating draft with AI…"):
                try:
                    if uploaded_image is not None:
                        file_record = client.upload_file(
                            token,
                            company_id,
                            uploaded_image.getvalue(),
                            uploaded_image.name,
                            uploaded_image.type or "image/jpeg",
                            kind="post_image",
                        )
                        payload["image_file_id"] = file_record["id"]
                    result = client.generate_post(token, company_id, payload)
                    st.session_state["last_generated_id"] = result["calendar_item"]["id"]
                    st.session_state.pop("edit_generated", None)
                    if result.get("slot_label"):
                        st.session_state["last_slot_label"] = result["slot_label"]
                    cal = result["calendar_item"]
                    if cal.get("scheduled_date"):
                        sched = cal["scheduled_date"]
                        if cal.get("scheduled_time"):
                            sched += f" at {cal['scheduled_time']}"
                        st.session_state["last_schedule_label"] = sched
                    st.rerun()
                except ApiError as exc:
                    if exc.status_code == 409 and "all_slots_filled_this_week" in str(exc):
                        st.session_state["show_next_week_offer"] = True
                        st.rerun()
                    else:
                        st.error(str(exc))

    if st.session_state.get("show_next_week_offer"):
        st.warning("All plan slots are filled for this week.")
        if st.button("Generate for next week", key="gen_next_week_btn"):
            st.session_state.pop("show_next_week_offer", None)
            st.session_state["pending_next_week_generate"] = True
            st.rerun()

    _render_last_generated(client, token, company_id)


def _build_payload(
    *,
    gen_mode: str,
    post_type: str,
    platform: str,
    content_idea: str,
    keywords: str,
    image_description: str,
    output_language: str,
    scheduled_date_value: date | None,
    scheduled_time_value: time | None,
    use_next_week: bool,
) -> dict:
    idea = content_idea.strip() or None
    base: dict = {
        "keywords": keywords.strip() or None,
        "image_description": image_description.strip() or None,
        "content_idea": idea,
        "output_language": output_language,
    }
    if gen_mode == "instant":
        base.update({"mode": "instant", "post_type": post_type, "platform": platform})
        return base
    if gen_mode == "manual":
        base.update(
            {
                "mode": "scheduled_manual",
                "post_type": post_type,
                "platform": platform,
                "scheduled_date": scheduled_date_value.isoformat() if scheduled_date_value else None,
                "scheduled_time": scheduled_time_value.strftime("%H:%M") if scheduled_time_value else None,
            }
        )
        return base
    base.update({"mode": "scheduled_follow_plan", "use_next_week": use_next_week})
    return base


def _company_has_posting_rules(client: ApiClient, token: str, company_id: int) -> bool:
    try:
        rules = client.list_posting_rules(token, company_id)
    except ApiError:
        return False
    return any(r.get("is_active", True) for r in rules)


def _render_follow_plan_context(client: ApiClient, token: str, company_id: int) -> bool:
    has_rules = _company_has_posting_rules(client, token, company_id)

    try:
        active_plan = client.get_active_marketing_plan(token, company_id)
    except ApiError as exc:
        st.warning(f"Could not load marketing plan: {exc}")
        active_plan = None

    if active_plan:
        st.markdown(f"**Active plan:** {active_plan['name']}")
        if active_plan.get("goals"):
            goals_preview = active_plan["goals"].strip().splitlines()[0][:160]
            st.caption(goals_preview + ("…" if len(active_plan["goals"]) > 160 else ""))
    elif has_rules:
        st.caption("Posting rules are configured; no active plan record found.")
    else:
        st.warning("No active marketing plan. Create one on the Marketing Plan page first.")

    _render_week_slots(client, token, company_id)
    return has_rules


def _render_week_slots(client: ApiClient, token: str, company_id: int) -> None:
    try:
        data = client.get_week_slots(token, company_id)
    except ApiError as exc:
        st.error(f"Could not load plan slots: {exc}")
        _render_posting_rules_fallback(client, token, company_id)
        return
    slots = data.get("slots") or []
    if not slots:
        st.info("No posting rules in your marketing plan for this week.")
        _render_posting_rules_fallback(client, token, company_id)
        return
    st.caption(f"Week {data['week_start']} → {data['week_end']}")
    next_empty = next((s for s in slots if not s["filled"]), None)
    if next_empty:
        day = _slot_day_label(next_empty)
        pillar = f" · {next_empty['pillar_name']}" if next_empty.get("pillar_name") else ""
        post_type = next_empty.get("post_type", "professional")
        st.success(
            f"**Next post will use:** {next_empty['platform'].title()} · {post_type} · "
            f"{day} {next_empty['post_time']}{pillar}"
        )
    for slot in slots:
        day = _slot_day_label(slot)
        label = f"{slot['platform'].title()} · {day} {slot['post_time']}"
        if slot.get("pillar_name"):
            label += f" · {slot['pillar_name']}"
        if slot["filled"]:
            status = (slot.get("status") or "filled").capitalize()
            hook = slot.get("hook_preview") or ""
            st.markdown(f"✓ **{label}** — {status}" + (f" ({hook[:40]}…)" if hook else ""))
        else:
            st.markdown(f"○ {label} — *available*")
    if data.get("all_filled"):
        st.warning("All slots filled this week. Generate will offer next week.")


def _slot_day_label(slot: dict) -> str:
    target = slot.get("target_date")
    if target:
        try:
            return WEEKDAYS[date.fromisoformat(str(target)).weekday()]
        except (ValueError, TypeError):
            pass
    return WEEKDAYS[slot["weekday"]]


def _render_posting_rules_fallback(client: ApiClient, token: str, company_id: int) -> None:
    try:
        rules = client.list_posting_rules(token, company_id)
    except ApiError:
        return
    active_rules = [r for r in rules if r.get("is_active", True)]
    if not active_rules:
        return
    st.caption("Weekly schedule from your plan:")
    for rule in active_rules:
        st.markdown(
            f"- {rule['platform'].title()} · {WEEKDAYS[rule['weekday']]} {rule['post_time']} "
            f"({rule['post_type']})"
        )


def _render_last_generated(client: ApiClient, token: str, company_id: int) -> None:
    last_id = st.session_state.get("last_generated_id")
    if not last_id:
        return

    try:
        items = client.list_calendar(token, company_id)
    except ApiError:
        return
    item = next((i for i in items if i["id"] == last_id), None)
    if item is None:
        st.session_state.pop("last_generated_id", None)
        return

    st.divider()
    st.subheader("Your new post")
    slot_label = st.session_state.pop("last_slot_label", None)
    schedule_label = st.session_state.pop("last_schedule_label", None)
    caption = f"Status: {item['status'].capitalize()} · **Publish to: {PLATFORM_LABELS.get(item['platform'], item['platform'].title())}**"
    caption += _schedule_caption(item)
    if slot_label:
        caption += f" · Plan slot: {slot_label}"
    elif schedule_label:
        caption += f" · Scheduled {schedule_label}"
    st.caption(caption)

    if item.get("scheduled_date") and item.get("posting_rule_id"):
        st.info(
            f"Queued for plan: **{item['platform'].title()}** on "
            f"**{item['scheduled_date']}** at **{item.get('scheduled_time') or 'plan time'}**"
        )

    img_b64, img_mime = load_post_image(client, token, company_id, item.get("image_file_id"))
    render_platform_preview(
        item["platform"],
        "Preview",
        item["content"],
        image_base64=img_b64,
        image_mime=img_mime,
    )

    if st.session_state.get("edit_generated"):
        st.divider()
        _render_edit_form(client, token, company_id, item)
        if st.button("Done editing", key="done_editing_btn"):
            st.session_state.pop("edit_generated", None)
            st.rerun()
        return

    st.divider()
    col_edit, col_queue, col_new = st.columns(3)

    if item["status"] in ("draft",):
        if col_edit.button("Edit post", key="edit_generated_btn", use_container_width=True):
            st.session_state["edit_generated"] = True
            st.rerun()
        if col_queue.button(
            "Queue post", key="queue_generated_btn", type="primary", use_container_width=True
        ):
            try:
                client.approve_calendar_item(token, company_id, item["id"])
                client.queue_calendar_item(token, company_id, item["id"])
                st.success("Post queued — find it in the Publishing Queue tab.")
                st.rerun()
            except ApiError as exc:
                st.error(str(exc))
    elif item["status"] == "queued":
        col_edit.info("Queued for publishing.")
        col_queue.empty()
    else:
        col_edit.caption(f"Status: {item['status']}")

    col_new.button(
        "Start new post",
        key="clear_generated_btn",
        use_container_width=True,
        on_click=_start_new_post,
    )


def _schedule_caption(item: dict) -> str:
    if not item.get("scheduled_date"):
        return ""
    label = f" · Scheduled {item['scheduled_date']}"
    if item.get("scheduled_time"):
        label += f" at {item['scheduled_time']}"
    return label


def _parse_time(value: str | None) -> time | None:
    if not value:
        return None
    try:
        hh, mm = value.split(":")[:2]
        return time(int(hh), int(mm))
    except (ValueError, TypeError):
        return None


def _render_edit_form(client: ApiClient, token: str, company_id: int, item: dict) -> None:
    content = item["content"]
    scheduled = item.get("scheduled_date")
    default_date = date.fromisoformat(scheduled) if scheduled else date.today()
    default_time = _parse_time(item.get("scheduled_time")) or time(9, 0)
    from_plan = bool(item.get("posting_rule_id"))

    sched_key = f"edit_use_schedule_{item['id']}"
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
            key=f"edit_sched_date_{item['id']}",
            disabled=from_plan,
        )
        scheduled_time = sched_col2.time_input(
            "Scheduled time",
            value=default_time,
            key=f"edit_sched_time_{item['id']}",
            disabled=from_plan,
        )

    with st.form(f"edit_form_{item['id']}"):
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
            client.update_calendar_item(token, company_id, item["id"], payload)
            st.success("Draft saved.")
            st.rerun()
        except ApiError as exc:
            st.error(str(exc))
