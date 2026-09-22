"""Surfer-dude / kite-bro / programmer-guru voice (facade).

Constants: ``voice_bank``. Picks: ``voice_pick``. Session copy: ``voice_lines``.
"""

from __future__ import annotations

from typing import Any

from guru.rider.voice_bank import (
    AGENT_PROMPT_TO_USER,
    BANNER_TAG,
    CALL,
    JOKES,
    NAME_LORE,
    TAGLINES,
    VOCABULARY,
    VOICE_ID,
    VOICE_RULE,
)
from guru.rider.voice_lines import (
    advice_summary,
    checklist,
    far_drive_note,
    hour_bits,
    incomplete_advice_summary,
    slot_line,
    thinking_headers,
    weekend_incomplete,
    weekend_summary,
)
from guru.rider.voice_pick import call_label, joke, tagline

__all__ = (
    "AGENT_PROMPT_TO_USER",
    "BANNER_TAG",
    "CALL",
    "JOKES",
    "NAME_LORE",
    "TAGLINES",
    "VOCABULARY",
    "VOICE_ID",
    "VOICE_RULE",
    "advice_summary",
    "call_label",
    "checklist",
    "far_drive_note",
    "hour_bits",
    "incomplete_advice_summary",
    "joke",
    "slot_line",
    "tagline",
    "thinking_headers",
    "voice_payload",
    "weekend_incomplete",
    "weekend_summary",
)


def voice_payload() -> dict[str, Any]:
    """Attach to instruct / MCP so every agent hosts the same register."""
    return {
        "id": VOICE_ID,
        "rule": VOICE_RULE,
        "calls": dict(CALL),
        "vocab": dict(VOCABULARY),
        "lore": dict(NAME_LORE),
        "taglines": list(TAGLINES),
        "jokes": {k: list(v) for k, v in JOKES.items()},
        "style": (
            "kite bro + surfer dude + programmer who rides -- same DNA as "
            "Windguru's name (Wind + Guru), beach edition"
        ),
        "examples": [
            "SEND IT Thu Castelldefels -- 14 gust 18, rig your 9, 4/3, beach check 5. "
            "Green build, green Gust -- merge to the beach.",
            "SOFT CALL -- juiced enough for a local foil lap, skip the 180 km haul. "
            "Flaky test: pass locally, fail on a long PR.",
            "SIT IT OUT -- dead zone in range; don't force a kitemare. "
            "404: wind not found.",
        ],
        "agent_hint": (
            "Narrate in this voice. Optionally drop one short joke from "
            "data.voice.jokes when the vibe fits -- never instead of the call, "
            "never stack three punchlines. Cite lore.windguru once if someone "
            "asks why it's called guru/Windguru."
        ),
    }
