import streamlit as st

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
WEEKDAYS_FULL = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
PLATFORM_EMOJI = {"linkedin": "in", "facebook": "f", "instagram": "ig"}


def render_plan_visual(plan: dict, pillars: list[dict], rules: list[dict]) -> None:
    """Native Streamlit visualization for an active marketing plan."""
    st.markdown(f"### {plan['name']}")
    status = plan.get("status", "draft").title()
    cols = st.columns(4)
    cols[0].metric("Status", status)
    cols[1].metric("Pillars", len(pillars))
    cols[2].metric("Schedule slots", len([r for r in rules if r.get("is_active", True)]))
    if plan.get("period_start") and plan.get("period_end"):
        cols[3].metric("Duration", f"{plan['period_start']} → {plan['period_end']}")
    elif plan.get("period_start"):
        cols[3].metric("Started", str(plan["period_start"]))
    else:
        cols[3].metric("Period", "—")

    if plan.get("notes"):
        with st.container(border=True):
            st.markdown("**Strategy summary**")
            st.markdown(plan["notes"])

    if plan.get("goals"):
        with st.container(border=True):
            st.markdown("**Goals**")
            for line in plan["goals"].splitlines():
                text = line.strip()
                if text:
                    st.markdown(f"- {text.lstrip('-•').strip()}")

    if pillars:
        st.markdown("#### Content pillars")
        total_weight = sum(p.get("weight", 1) for p in pillars) or 1
        for pillar in pillars:
            weight = pillar.get("weight", 5)
            pct = weight / total_weight
            st.markdown(f"**{pillar['name']}** · weight {weight}")
            if pillar.get("description"):
                st.caption(pillar["description"])
            st.progress(min(1.0, pct), text=f"{int(pct * 100)}% focus")

    active_rules = [r for r in rules if r.get("is_active", True)]
    if active_rules:
        st.markdown("#### Weekly schedule")
        schedule_rows = []
        for rule in active_rules:
            schedule_rows.append(
                {
                    "Platform": rule["platform"].title(),
                    "Day": WEEKDAYS_FULL[rule["weekday"]],
                    "Time": rule["post_time"],
                    "Type": rule["post_type"],
                    "Frequency": rule["frequency"],
                }
            )
        st.dataframe(schedule_rows, use_container_width=True, hide_index=True)

        st.markdown("#### Schedule grid")
        grid_cols = st.columns(7)
        for i, day in enumerate(WEEKDAYS):
            with grid_cols[i]:
                st.caption(f"**{day}**")
                day_rules = [r for r in active_rules if r["weekday"] == i]
                if not day_rules:
                    st.write("—")
                for rule in day_rules:
                    plat = rule["platform"][:2].upper()
                    st.markdown(f"`{plat}` {rule['post_time']}")
