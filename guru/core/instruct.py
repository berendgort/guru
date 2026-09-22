"""Agent recipe text (CLI ``instruct`` + MCP)."""

from __future__ import annotations

from typing import Any

from guru.rider.intake import intake_payload
from guru.rider.profile_store import load_profile, profile_payload

INSTRUCT_STEPS: list[dict[str, Any]] = [
    {
        "step": 0,
        "action": "first_pass_intake",
        "command": "guru profile --json   # if ready=false → show data.intake.prompt_to_user",
        "detail": (
            "FIRST PASS ONLY: if profile not ready or not range_ready, show "
            "intake.prompt_to_user to the human ONCE. They reply with one "
            "key=value line. Then: guru setup --intake '<paste>' --json. "
            "Never drip-feed questions field-by-field."
        ),
    },
    {
        "step": 1,
        "action": "search_spots",
        "command": 'guru spots "<name>" --json',
        "detail": (
            "Search named Windguru spots. If multiple matches, pick an id "
            "(do not guess)."
        ),
    },
    {
        "step": 2,
        "action": "near_spots",
        "command": "guru near --lat <lat> --lon <lon> --json",
        "detail": (
            "Or find free named spots near coordinates (map markers). "
            "Never use PRO lat/lon click-forecast."
        ),
    },
    {
        "step": 3,
        "action": "weekend_or_best",
        "command": "guru weekend --json   # or: guru best <id> --advise --json",
        "detail": (
            "Ask 'where can I kite this weekend?' → guru weekend (ranks drive-range "
            "spots; far trips need clear GO). Single spot → best --advise "
            "(kite size, gust quality, 2–4h wetsuit)."
        ),
    },
    {
        "step": 4,
        "action": "think_like_a_kiter",
        "command": None,
        "detail": (
            "Narrate data.advice / weekend.spots: size for gusts, smooth vs gusty, "
            "suit for session length + wind chill, side-shore preference, "
            "confirm at beach 5 min. Ignore lower-weighted models unless asked."
        ),
    },
]

INSTRUCT_SUMMARY = (
    "First pass: one efficient intake (sport/weight/quiver/suits/home range), "
    "then weekend or best --advise. WINDGURU_DEFAULT only. Think like a kiter. "
    "No HTML scrape. No PRO."
)


def instruct_payload() -> dict[str, Any]:
    try:
        status = profile_payload(load_profile())
        need_intake = not (status["ready"] and status["range_ready"])
    except Exception:
        status = None
        need_intake = True

    return {
        "summary": INSTRUCT_SUMMARY,
        "preset": "WINDGURU_DEFAULT",
        "top_models": 3,
        "first_pass": need_intake,
        "intake": intake_payload(needed=need_intake),
        "profile_status": status,
        "steps": INSTRUCT_STEPS,
        "examples": [
            "guru profile --json",
            (
                "guru setup --intake 'sport=kitefoil weight=78 kites=7,9,12 "
                "wetsuits=3/2,4/3 session=3 home=41.39,2.17 drive_km=200 "
                "range=Trabucador → Leucate' --json"
            ),
            "guru weekend --json",
            "guru best 201 --advise --json",
        ],
        "profile": {
            "path": "~/.config/guru/profile.json",
            "fields": [f["key"] for f in intake_payload()["fields"]],
            "sports": ["kitesurf", "kitefoil", "surfkite"],
        },
    }
