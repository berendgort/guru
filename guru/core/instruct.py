"""Agent recipe text (CLI ``instruct`` + MCP)."""

from __future__ import annotations

from typing import Any

INSTRUCT_STEPS: list[dict[str, Any]] = [
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
        "action": "best_forecast",
        "command": "guru best <id_spot> --json",
        "detail": (
            "Uses Tune preset WINDGURU_DEFAULT only: compute model weights "
            "(resolution × freshness × preference), keep top 3, fetch those forecasts."
        ),
    },
    {
        "step": 4,
        "action": "ignore_rest",
        "command": None,
        "detail": (
            "Ignore lower-weighted models unless the user asks for a specific "
            "model via guru forecast -m."
        ),
    },
]

INSTRUCT_SUMMARY = (
    "For any place: resolve a named Windguru spot, then run guru best. "
    "Always WINDGURU_DEFAULT Tune; trust only the top 3 models by weight. "
    "Do not scrape windguru.cz HTML or the map canvas. Do not require PRO."
)


def instruct_payload() -> dict[str, Any]:
    return {
        "summary": INSTRUCT_SUMMARY,
        "preset": "WINDGURU_DEFAULT",
        "top_models": 3,
        "steps": INSTRUCT_STEPS,
        "examples": [
            'guru spots "castelldefels" --json',
            "guru best 201 --json",
            'guru spots "De Slufter" --json',
            "guru best 48309 -H 24 --json",
            "guru near --lat 51.9 --lon 4.1 --radius 40 --json",
        ],
    }
