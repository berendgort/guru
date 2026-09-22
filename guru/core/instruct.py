"""Agent recipe text (CLI ``instruct`` + MCP)."""

from __future__ import annotations

from typing import Any

from guru.core.upgrade import upgrade_status
from guru.core.wire import wire_status
from guru.rider.intake import intake_payload
from guru.rider.profile_store import load_profile, profile_payload

INSTRUCT_STEPS: list[dict[str, Any]] = [
    {
        "step": 0,
        "action": "auto_upgrade",
        "command": (
            "pipx upgrade windguru   # or: pip install -U 'windguru[mcp]'"
        ),
        "detail": (
            "EVERY SESSION: check data.upgrade.update_available (or guru doctor "
            "--json). If true, upgrade windguru on the fly before briefing — "
            "do not leave the user on a stale CLI."
        ),
    },
    {
        "step": 0,
        "action": "auto_wire_mcp",
        "command": "guru wire --json   # also: guru doctor --json (wires by default)",
        "detail": (
            "TURBO AUTOMATION: YOU run guru wire / doctor yourself. Never ask "
            "the human to edit Claude/Cursor config, run guru-mcp-tunnel, or "
            "paste connector URLs. Local STDIO guru-mcp has full network "
            "(Windguru works). Prefer MCP tools after wire; if shell cannot "
            "reach windguru.cz, do NOT invent forecasts — use wired MCP or "
            "local guru CLI on the user's machine. Restart client once only "
            "if tools missing after first wire."
        ),
    },
    {
        "step": 1,
        "action": "first_pass_intake",
        "command": "guru profile --json   # if ready=false → show data.intake.prompt_to_user",
        "detail": (
            "FIRST USER MESSAGE: if profile not ready or not range_ready, show "
            "intake.prompt_to_user to the human ONCE (must include level — it "
            "changes GO wind and sizing). They reply with one key=value line. "
            "Then: guru setup --intake '<paste>' --json. Never drip-feed "
            "questions. Never skip to weekend/best without a ready profile."
        ),
    },
    {
        "step": 2,
        "action": "weekend_or_best",
        "command": "guru weekend --json   # or: guru best <id> --json  (advice on by default)",
        "detail": (
            "Ask 'where can I kite?' → guru weekend (default ~96h + top-3 "
            "models). Narrate data.schedule day-by-day (Tue/Wed/Thu…) — do not "
            "wait for the rider to ask about Thursday. Far trips need clear GO. "
            "Named spot → guru best <id>."
        ),
    },
    {
        "step": 3,
        "action": "resolve_spot_if_needed",
        "command": 'guru spots "<name>" --json   # or: guru near --lat --lon --json',
        "detail": (
            "If you need an id: search named spots or free map markers near "
            "coords. On ambiguous, pick from candidates — never silent "
            "first-match. Never use PRO lat/lon click-forecast."
        ),
    },
    {
        "step": 4,
        "action": "think_like_a_kiter",
        "command": None,
        "detail": (
            "Narrate schedule + spots: size for gusts, model_agree, suit for "
            "session length, beach 5 min check. Lead with the week plan, not "
            "only today's best spot."
        ),
    },
]

INSTRUCT_SUMMARY = (
    "Upgrade + auto-wire MCP (guru wire / doctor) yourself — never ask the "
    "human to run tunnel/config commands. FIRST MESSAGE: collect rider "
    "profile once (sport, weight, LEVEL, quiver, suits, home range). Then "
    "weekend (~4-day schedule + top-3 models) or best. Narrate the week. "
    "WINDGURU_DEFAULT only. No HTML scrape. No PRO."
)


def instruct_payload() -> dict[str, Any]:
    try:
        status = profile_payload(load_profile())
        need_intake = not (status["ready"] and status["range_ready"])
    except Exception:
        status = None
        need_intake = True

    upgrade = upgrade_status()
    return {
        "summary": INSTRUCT_SUMMARY,
        "preset": "WINDGURU_DEFAULT",
        "top_models": 3,
        "weekend_hours": 96,
        "first_pass": need_intake,
        "upgrade": upgrade,
        "mcp_wire": wire_status(),
        "intake": intake_payload(needed=need_intake),
        "profile_status": status,
        "steps": INSTRUCT_STEPS,
        "automation": {
            "rule": "agent_runs_all_commands",
            "human_runs": [],
            "agent_runs": [
                "pipx upgrade windguru",
                "guru wire --json",
                "guru doctor --json",
                "guru setup --intake …",
                "guru weekend --json",
                "guru best <id> --json",
            ],
            "never_ask_human": [
                "edit Claude/Cursor MCP config",
                "run guru-mcp-tunnel",
                "paste Cloudflare connector URLs",
                "install cloudflared",
            ],
        },
        "examples": [
            "pipx upgrade windguru",
            "guru wire --json",
            "guru profile --json",
            (
                "guru setup --intake 'sport=kitefoil weight=78 level=intermediate "
                "kites=7,9,12 wetsuits=3/2,4/3 session=3 home=41.39,2.17 "
                "drive_km=200 range=Trabucador → Leucate' --json"
            ),
            "guru weekend --json",
            "guru best 201 --json",
        ],
        "profile": {
            "path": "~/.config/guru/profile.json",
            "fields": [f["key"] for f in intake_payload()["fields"]],
            "sports": ["kitesurf", "kitefoil", "surfkite"],
        },
    }
