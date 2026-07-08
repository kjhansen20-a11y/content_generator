"""Platform-specific optimal posting windows for plan generation and scheduling."""

from app.models.content import Platform

# weekday 0=Monday … 6=Sunday. Times are HH:MM in 24h format.
LINKEDIN_OPTIMAL_BY_WEEKDAY: dict[int, str] = {
    0: "11:00",  # Monday — high engagement late morning
    1: "10:00",  # Tuesday — peak 10:00–12:00
    2: "10:00",  # Wednesday — peak 08:00–14:00
    3: "10:00",  # Thursday — peak 09:00–14:00
    4: "09:00",  # Friday — high engagement mornings
    5: "10:00",  # Saturday — moderate late morning
    6: "10:00",  # Sunday — lowest day; morning if needed
}

FACEBOOK_OPTIMAL_BY_WEEKDAY: dict[int, str] = {
    0: "09:00",
    1: "10:00",
    2: "11:00",
    3: "11:00",
    4: "09:00",
    5: "10:00",
    6: "12:00",
}

INSTAGRAM_OPTIMAL_BY_WEEKDAY: dict[int, str] = {
    0: "11:00",
    1: "11:00",
    2: "11:00",
    3: "12:00",
    4: "11:00",
    5: "10:00",
    6: "10:00",
}

_PLATFORM_DEFAULTS: dict[Platform, dict[int, str]] = {
    Platform.linkedin: LINKEDIN_OPTIMAL_BY_WEEKDAY,
    Platform.facebook: FACEBOOK_OPTIMAL_BY_WEEKDAY,
    Platform.instagram: INSTAGRAM_OPTIMAL_BY_WEEKDAY,
}

LINKEDIN_ENGAGEMENT_GUIDANCE = """LinkedIn global engagement (Sprout Social heatmap):
- Peak: Tuesday 10:00–12:00, Wednesday 08:00–14:00, Thursday 09:00–14:00
- High: Monday 11:00 & 13:00–14:00; Tuesday 07:00–09:00 & 13:00–14:00; Wednesday 07:00 & 15:00;
  Thursday 06:00–08:00 & 15:00; Friday 07:00–12:00; Saturday ~09:00–13:00
- Avoid: 22:00–04:00 every day; minimize Sunday posting
- Prefer weekdays Tue–Thu for highest reach; set post_time inside peak/high windows"""


def optimal_time_for_slot(platform: Platform, weekday: int) -> str:
    weekday = max(0, min(6, weekday))
    defaults = _PLATFORM_DEFAULTS.get(platform, LINKEDIN_OPTIMAL_BY_WEEKDAY)
    return defaults.get(weekday, "10:00")


def optimal_posting_guidance_block(platforms: list[Platform] | None = None) -> str:
    lines = [
        "Use research-backed optimal posting windows when setting post_time on each posting_rule.",
        LINKEDIN_ENGAGEMENT_GUIDANCE,
    ]
    platform_set = set(platforms or [Platform.linkedin])
    if Platform.facebook in platform_set:
        lines.append(
            "Facebook: weekdays 09:00–12:00 and 13:00–15:00 tend to perform best; avoid late night."
        )
    if Platform.instagram in platform_set:
        lines.append(
            "Instagram: weekdays late morning (11:00–13:00) and early evening (18:00–20:00) perform well."
        )
    lines.append(
        "Each posting_rule post_time must fall inside the optimal window for that platform and weekday. "
        "Prefer Tuesday–Thursday for LinkedIn when spreading slots across the week."
    )
    return "\n".join(lines)
