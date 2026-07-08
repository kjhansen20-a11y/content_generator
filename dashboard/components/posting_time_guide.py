from pathlib import Path

import streamlit as st

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"
LINKEDIN_HEATMAP = ASSETS_DIR / "linkedin-engagement-heatmap.png"

LINKEDIN_TIPS = """
**LinkedIn peak engagement (Sprout Social)**
- **Best days:** Tuesday, Wednesday, Thursday
- **Peak windows:** Tue 10:00–12:00 · Wed 08:00–14:00 · Thu 09:00–14:00
- **Also strong:** Fri 07:00–12:00 · Mon 11:00 & 13:00–14:00
- **Avoid:** 22:00–04:00 · Sundays (lowest engagement)
"""

PLATFORM_TIPS: dict[str, str] = {
    "linkedin": LINKEDIN_TIPS,
    "facebook": """
**Facebook**
- Weekdays **09:00–12:00** and **13:00–15:00** typically perform best.
- Avoid late-night slots.
""",
    "instagram": """
**Instagram**
- **Late morning** (11:00–13:00) and **early evening** (18:00–20:00) on weekdays are strong.
- Weekends: late morning tends to work better than evenings.
""",
}


def render_posting_time_guide(platform: str) -> None:
    """Show optimal posting-time reference when the user picks date & time manually."""
    with st.expander("Optimal posting times", expanded=platform == "linkedin"):
        if platform == "linkedin" and LINKEDIN_HEATMAP.exists():
            st.image(
                str(LINKEDIN_HEATMAP),
                caption="LinkedIn global engagement by day and hour (Sprout Social)",
                use_container_width=True,
            )
        st.markdown(PLATFORM_TIPS.get(platform, LINKEDIN_TIPS))
        suggested = _suggested_time(platform)
        if suggested:
            st.caption(f"Suggested default for today: **{suggested}**")


def _suggested_time(platform: str) -> str:
    from datetime import date

    weekday = date.today().weekday()
    defaults: dict[str, dict[int, str]] = {
        "linkedin": {0: "11:00", 1: "10:00", 2: "10:00", 3: "10:00", 4: "09:00", 5: "10:00", 6: "10:00"},
        "facebook": {0: "09:00", 1: "10:00", 2: "11:00", 3: "11:00", 4: "09:00", 5: "10:00", 6: "12:00"},
        "instagram": {0: "11:00", 1: "11:00", 2: "11:00", 3: "12:00", 4: "11:00", 5: "10:00", 6: "10:00"},
    }
    times = defaults.get(platform, defaults["linkedin"])
    day = WEEKDAYS[weekday]
    return f"{day} at {times.get(weekday, '10:00')}"
