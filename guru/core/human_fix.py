"""Rare human UI fixes — only when the agent cannot automate.

Agents must run ``guru unlock`` / wire themselves first. Paste a
``say_to_rider`` block only when local writes are impossible or still
blocked (cloud environment UI, admin-locked toggle). Never invent steps.
"""

from __future__ import annotations

from typing import Any

from guru.core.wire import WINDGURU_CLOUD_DOMAINS, WINDGURU_HOSTS

_DOMAINS_CSV = ", ".join(WINDGURU_CLOUD_DOMAINS)
_CLAUDE_CSV = ", ".join(WINDGURU_HOSTS)


def human_fix_payload() -> dict[str, Any]:
    """Machine-readable rare-path recipes for instruct / unlock."""
    return {
        "policy": (
            "Automate everything first (upgrade, unlock, setup, weekend). "
            "Ask the human ONLY when this process cannot write their app "
            "settings — then paste the matching say_to_rider block EXACTLY. "
            "Never ask for pipx, shell guru, MCP JSON, or tunnels."
        ),
        "ask_human_only_when": [
            "no local shell to run guru unlock on the rider's machine",
            "unlock wrote settings but charts still gated (cloud/managed policy)",
            "ChatGPT Work / Codex cloud environment internet is off (UI-only)",
            "company admin locked the network toggle",
        ],
        "never_ask_human": [
            "install or upgrade windguru / pipx",
            "run any guru command",
            "edit MCP JSON by hand",
            "run cloudflared / guru-mcp-tunnel",
            "paste CLI JSON dumps",
        ],
        "recipes": {
            "restart_after_unlock": {
                "id": "restart_after_unlock",
                "when": "guru unlock just succeeded on this laptop",
                "say_to_rider": (
                    "Wind's unlocked on your laptop. One step left: start a "
                    "**new chat** in this app (close this one → New chat), "
                    "then ask: where can I kite?"
                ),
            },
            "chatgpt_work_network": {
                "id": "chatgpt_work_network",
                "when": (
                    "ChatGPT Work code/shell cannot reach Windguru "
                    "(Settings toggle — agent cannot flip it)"
                ),
                "say_to_rider": (
                    "Quick fix in ChatGPT Work (one toggle):\n"
                    "1. Open **Settings → Data controls → Work network access**\n"
                    "2. Turn **ON** “Allow public internet access”\n"
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
                    "Codex / ChatGPT cloud Environment — Agent internet "
                    "access is Off or Windguru missing from the allowlist"
                ),
                "domains": list(WINDGURU_CLOUD_DOMAINS),
                "say_to_rider": (
                    "Quick fix in Codex cloud (~30 seconds):\n"
                    "1. Open **Environments** → select the environment this "
                    "chat uses → **Internet access** / Agent internet\n"
                    "2. Set Agent internet access → **On**\n"
                    "3. Domain allowlist → add these exactly "
                    "(copy-paste):\n"
                    f"   `{_DOMAINS_CSV}`\n"
                    "4. Allowed methods: **GET, HEAD, OPTIONS** is enough\n"
                    "5. Start a **new chat** → ask: where can I kite?\n"
                    "Faster option: open **Cursor on this laptop** and ask there."
                ),
            },
            "claude_network_settings": {
                "id": "claude_network_settings",
                "when": (
                    "Claude still gated after unlock (managed policy / "
                    "claude.ai cloud) — agent cannot write settings"
                ),
                "domains": list(WINDGURU_HOSTS),
                "say_to_rider": (
                    "Quick fix in Claude:\n"
                    "1. In Claude Code type **/config** → open the "
                    "**Sandbox** tab → **Network → Allowed domains**\n"
                    "   (or on claude.ai: Settings → Claude Code)\n"
                    "2. Add these domains exactly:\n"
                    f"   `{_CLAUDE_CSV}`\n"
                    "3. Start a **new chat** → ask: where can I kite?\n"
                    "Faster option: open **Cursor on this laptop** and ask there."
                ),
            },
            "fallback_cursor": {
                "id": "fallback_cursor",
                "when": (
                    "any host still blocked, or the rider cannot change "
                    "settings — always safe"
                ),
                "say_to_rider": (
                    "Yo — this chat can't open the wind charts. Fastest path: "
                    "open **Cursor on this laptop** and ask “where can I kite?” "
                    "— same quiver, live wind, no settings hunt."
                ),
            },
        },
    }


def pick_human_fix(
    *,
    host_hint: str | None = None,
    after_unlock: bool = False,
    still_blocked: bool = False,
) -> dict[str, Any] | None:
    """Choose one rare recipe. Returns None when the agent should keep automating."""
    recipes = human_fix_payload()["recipes"]
    if after_unlock and not still_blocked:
        return recipes["restart_after_unlock"]
    if not still_blocked and not after_unlock:
        return None
    hint = (host_hint or "").lower()
    if "chatgpt" in hint or "work" in hint:
        return recipes["chatgpt_work_network"]
    if "codex" in hint or "openai" in hint:
        return recipes["codex_cloud_environment"]
    if "claude" in hint or "anthropic" in hint:
        return recipes["claude_network_settings"]
    return recipes["fallback_cursor"]
