"""Enrich allowlist / sandbox-gated failures for agents."""

from __future__ import annotations

__all__ = ("gated_fields", "is_gated")

from typing import Any


def is_gated(exc: BaseException) -> bool:
    msg = str(exc).lower()
    status = getattr(exc, "status_code", None)
    return (
        status == 403
        or "allowlist" in msg
        or "charts gated" in msg
        or "unlock_already_done" in msg
        or "blocked in this runtime" in msg
        or "windguru gated" in msg
        or ("unreachable" in msg and "windguru" in msg)
    )


def gated_fields(*, unlock_already_done: bool | None = None) -> dict[str, Any]:
    """Attach rider_facing + recipe so agents do not invent /config steps."""
    from guru.core.human_fix import pick_human_fix
    from guru.core.wire import wire_status

    written = bool(wire_status().get("windguru_unlocked"))
    if unlock_already_done is not None:
        written = bool(unlock_already_done) or written

    if not written:
        return {
            "error_type": "network_gated",
            "network": {"reachable": False, "unlock_already_done": False},
            "human_fix": None,
            "say_to_rider": None,
            "rider_facing": None,
            "agent_next": ["run_guru_unlock_json_once", "then_show_rider_facing"],
            "agent_note": (
                "Charts gated and allowlist not written. YOU run "
                "`guru unlock --json` once now. Do not ask the rider. Do not "
                "show /config yet. No jq."
            ),
        }

    recipe = pick_human_fix(
        after_unlock=True,
        still_blocked=True,
        allowlist_written=True,
    )
    text = (recipe or {}).get("say_to_rider") or (
        "Open a new chat, then ask where you can kite."
    )
    return {
        "error_type": "network_gated",
        "network": {"reachable": False, "unlock_already_done": True},
        "human_fix": recipe,
        "say_to_rider": text,
        "rider_facing": {
            "kind": "user_visible_copy",
            "not_system_prompt": True,
            "text": text,
        },
        "agent_next": [
            "show_rider_facing_text_once",
            "never_unlock_again",
            "never_invent_config_domain_steps",
            "stop_until_new_chat_or_cursor",
        ],
        "agent_note": (
            "Show rider_facing.text once (UX copy, not a system prompt). "
            "Allowlist already written -- never unlock again, never /config "
            "Allowed domains. No jq."
        ),
    }
