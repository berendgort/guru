"""Rare human UI fixes -- only when the agent cannot automate.

Agents must run ``guru unlock`` themselves first. Show a ``say_to_rider``
block only when local writes are impossible or a new chat after unlock is
still gated. Never invent steps. Never depend on ``jq``.
"""

from __future__ import annotations

from typing import Any

from guru.core.hosts import WINDGURU_CLOUD_DOMAINS, WINDGURU_HOSTS

__all__ = ("human_fix_payload", "pick_human_fix")

_DOMAINS_CSV = ", ".join(WINDGURU_CLOUD_DOMAINS)
_CLAUDE_CSV = ", ".join(WINDGURU_HOSTS)


def human_fix_payload() -> dict[str, Any]:
    """Machine-readable rare-path recipes for instruct / unlock."""
    return {
        "policy": (
            "Automate first (upgrade, unlock once, setup, weekend). Ask the "
            "human ONLY when this process cannot open charts -- show the "
            "matching say_to_rider EXACTLY. Never ask for pipx, shell, jq, "
            "MCP JSON, or tunnels."
        ),
        "ask_human_only_when": [
            "no local shell to run guru unlock",
            "unlock wrote allowlist but THIS process still gated "
            "(need new chat -- use restart_after_unlock, not /config)",
            "new chat after unlock still gated (cloud hard block -- Cursor)",
            "ChatGPT Work / Codex cloud internet toggle is UI-only",
            "company admin locked the network toggle",
        ],
        "never_ask_human": [
            "install or upgrade windguru / pipx",
            "run any guru command",
            "edit MCP JSON by hand",
            "run cloudflared / guru-mcp-tunnel",
            "paste CLI JSON dumps",
            "install jq",
        ],
        "recipes": {
            "restart_after_unlock": {
                "id": "restart_after_unlock",
                "when": (
                    "unlock wrote allowlist (claude_unlocked true) but this "
                    "process is still gated -- domains need a new chat"
                ),
                "kind": "user_visible_copy",
                "say_to_rider": (
                    "Wind allowlist is patched on this machine. One step "
                    "left: open a **new chat**, then ask where you can kite. "
                    "No Settings hunt -- domains are already written."
                ),
            },
            "chatgpt_work_network": {
                "id": "chatgpt_work_network",
                "when": (
                    "ChatGPT Work code/shell cannot reach Windguru "
                    "(Settings toggle -- agent cannot flip it)"
                ),
                "say_to_rider": (
                    "Can't reach the wind temple from this Work chat -- "
                    "quick fix (one toggle):\n"
                    "1. Open **Settings -> Data controls -> Work network access**\n"
                    "2. Turn **ON** \"Allow public internet access\"\n"
                    "3. Wait for the current run to finish, then start a "
                    "**new Work chat**\n"
                    "4. Ask: where can I kite?\n"
                    "If that toggle is greyed out (company lock), open "
                    "**Cursor on this laptop** and ask the same question there."
                ),
            },
            "codex_cloud_environment": {
                "id": "codex_cloud_environment",
                "when": (
                    "Codex / ChatGPT cloud Environment -- Agent internet "
                    "access is Off or Windguru missing from the allowlist"
                ),
                "domains": list(WINDGURU_CLOUD_DOMAINS),
                "say_to_rider": (
                    "Cloud sandbox ate the wind packets -- quick fix in Codex "
                    "(~30 seconds):\n"
                    "1. Open **Environments** -> select the environment this "
                    "chat uses -> **Internet access** / Agent internet\n"
                    "2. Set Agent internet access -> **On**\n"
                    "3. Domain allowlist -> add these exactly "
                    "(copy-paste):\n"
                    f"   `{_DOMAINS_CSV}`\n"
                    "4. Allowed methods: **GET, HEAD, OPTIONS** is enough\n"
                    "5. Start a **new chat** -> ask: where can I kite?\n"
                    "Faster option: open **Cursor on this laptop** and ask there."
                ),
            },
            "claude_network_settings": {
                "id": "claude_network_settings",
                "when": (
                    "Claude allowlist NOT written yet and agent cannot write "
                    "~/.claude/settings.json (rare). If claude_unlocked is "
                    "already true, use restart_after_unlock or fallback_cursor "
                    "-- never this recipe."
                ),
                "domains": list(WINDGURU_HOSTS),
                "say_to_rider": (
                    "Claude could not write the Windguru allowlist for you -- "
                    "fastest path: open **Cursor on this laptop** and ask "
                    "\"where can I kite?\".\n"
                    "Optional on Claude Code desktop only: **/config** -> "
                    "Sandbox -> Network -> Allowed domains -> add:\n"
                    f"   `{_CLAUDE_CSV}`\n"
                    "then a **new chat**. Cloud sandboxes often ignore that UI."
                ),
            },
            "fallback_cursor": {
                "id": "fallback_cursor",
                "when": (
                    "new chat after unlock still gated, or any hard cloud "
                    "block -- always safe"
                ),
                "say_to_rider": (
                    "Yo -- this chat's sandbox still blocks Windguru even "
                    "after unlock (cloud isolation). Fastest path: open "
                    "**Cursor on this laptop** and ask \"where can I kite?\" "
                    "-- same quiver, live wind, no settings hunt."
                ),
            },
        },
    }


def pick_human_fix(
    *,
    host_hint: str | None = None,
    after_unlock: bool = False,
    still_blocked: bool = False,
    allowlist_written: bool = False,
) -> dict[str, Any] | None:
    """Choose one rare recipe. Returns None when the agent should keep automating."""
    recipes = human_fix_payload()["recipes"]
    if after_unlock and allowlist_written:
        # Domains are on disk; this process may stay gated until a new chat.
        return recipes["restart_after_unlock"]
    if after_unlock and not still_blocked:
        return recipes["restart_after_unlock"]
    if not still_blocked and not after_unlock:
        return None
    if allowlist_written:
        return recipes["fallback_cursor"]
    hint = (host_hint or "").lower()
    if "chatgpt" in hint or "work" in hint:
        return recipes["chatgpt_work_network"]
    if "codex" in hint or "openai" in hint:
        return recipes["codex_cloud_environment"]
    if "claude" in hint or "anthropic" in hint:
        return recipes["claude_network_settings"]
    return recipes["fallback_cursor"]
