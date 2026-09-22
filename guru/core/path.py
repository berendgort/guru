"""Universal agent path + Windguru reachability probe.

One rule for every host (Cursor, Claude, Codex, ChatGPT, shell bots):

  Run ``guru … --json`` (or local STDIO ``guru-mcp``) on a machine that can
  reach Windguru. Same CLI. Same JSON envelope. No per-app tunnels.

Cloud sandboxes that block windguru.cz cannot be fixed by MCP config files --
move the agent to a local/host process, or stop. Never invent forecasts.
"""

from __future__ import annotations

__all__ = (
    "agent_path_payload",
    "probe_windguru",
)

from typing import Any

from guru.core.wire import resolve_guru_mcp, wire_status


def probe_windguru() -> dict[str, Any]:
    """Can this process dial Windguru? Uses the same HTTP stack as forecasts."""
    try:
        from guru.search.client import IAPI_CZ, get_client

        get_client().get_json(
            params={"q": "search_spots", "search": "foster"},
            referer="https://www.windguru.cz/",
            base=IAPI_CZ,
        )
        return {"ok": True, "host": "www.windguru.cz", "reachable": True}
    except Exception as exc:  # noqa: BLE001 -- probe must never raise
        return {
            "ok": False,
            "host": "www.windguru.cz",
            "reachable": False,
            "error": f"{type(exc).__name__}: {exc}",
            "fix": (
                "Wind charts are gated. Agent: automate first -- run "
                "`guru unlock --json` on the rider's laptop if you have "
                "shell. Then paste unlock.say_to_rider (new chat). If you "
                "cannot unlock or still blocked: paste exactly one "
                "human_fix recipe say_to_rider for this host "
                "(ChatGPT Work / Codex cloud / Claude / Cursor fallback). "
                "Never ask for pipx or shell."
            ),
            "human_runs": [],
            "agent_must_not": [
                "ask human to pipx install / upgrade",
                "ask human to run guru setup/weekend/best",
                "invent Settings paths (use human_fix recipes only)",
                "say 'you'll need to run' / tutor sandboxes",
                "invent wind/kite advice without live data",
            ],
        }


def agent_path_payload() -> dict[str, Any]:
    """Machine-readable universal path for instruct / doctor."""
    mcp = resolve_guru_mcp()
    return {
        "id": "local_guru_cli",
        "summary": (
            "Install windguru once, then every app uses the same local CLI "
            "(`guru … --json`). Optional local STDIO MCP (`guru-mcp`) is the "
            "same library for hosts that spawn MCP -- not a second product."
        ),
        "install": "pipx install 'windguru[mcp]'",
        "commands": {
            "doctor": "guru doctor --json",
            "intake": "guru setup --intake '…' --json",
            "weekend": "guru weekend --json",
            "best": "guru best <id> --json",
        },
        "mcp_optional": {
            "stdio": "guru-mcp",
            "when": (
                "ONLY if shell `guru` is unavailable AND the host needs local "
                "STDIO MCP with guru missing -- never every session"
            ),
            "wire": "guru wire --json  # opt-in; doctor does not wire by default",
            "resolved": mcp,
            "status": wire_status(),
        },
        "unsupported": [
            "Relying on cloud sandbox shell to dial windguru.cz",
            "Wiring MCP or starting tunnels on every session",
            "Per-app Cloudflare tunnels / pasted connector URLs as the default path",
            "Asking the human to edit MCP JSON or run install commands",
        ],
        "rule": "agent_runs_all_commands",
    }
