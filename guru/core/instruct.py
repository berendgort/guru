"""Agent recipe text (CLI ``instruct`` + MCP)."""

from __future__ import annotations

from typing import Any

from guru.core.path import agent_path_payload, probe_windguru
from guru.core.upgrade import upgrade_status
from guru.rider.intake import intake_payload
from guru.rider.profile_store import load_profile, profile_payload
from guru.rider.voice import voice_payload

INSTRUCT_STEPS: list[dict[str, Any]] = [
    {
        "step": 0,
        "action": "auto_upgrade",
        "command": (
            "pipx upgrade windguru || pipx install --force 'windguru[mcp]'"
        ),
        "detail": (
            "EVERY SESSION: if data.upgrade.update_available (PyPI *newer* than "
            "installed), upgrade before briefing. Never downgrade if installed "
            "is ahead of a stale pypi_latest. Need >= 0.3.12 for kite-bro voice."
        ),
    },
    {
        "step": 0,
        "action": "universal_local_path",
        "command": "guru doctor --json   # probe + upgrade; do NOT pass --wire",
        "detail": (
            "ONE PATH FOR EVERY APP: local `guru … --json` on a machine that "
            "reaches Windguru. YOU run all commands — human_runs is always []. "
            "If data.network.reachable is false: follow data.on_unreachable "
            "exactly (intake → you run setup → say_exactly only). NEVER ask the "
            "human to install/run guru, never 'you'll need to run', never tutor. "
            "Wire/tunnel ONLY if shell guru is unavailable AND a local "
            "STDIO MCP host needs guru missing — never by default."
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
            "questions. Never skip to weekend/best without a ready profile. "
            "If network unreachable: still intake + YOU run setup; then only "
            "on_unreachable.say_exactly."
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
            "Narrate like a kite bro (data.voice): SEND IT / SOFT CALL / "
            "SIT IT OUT. Lead with week plan + spot + kite + suit; size for "
            "gusts; model_agree; beach 5 min check. Never dump raw model tables. "
            "Honesty > hype — long haul only on clear SEND IT."
        ),
    },
]

INSTRUCT_SUMMARY = (
    "Universal path: local guru CLI on a host that reaches Windguru. "
    "Voice: kite bro (SEND IT / SOFT CALL / SIT IT OUT) — honest, never hype "
    "a long haul. Wire/tunnel ONLY if CLI cannot run. Agent runs "
    "doctor/setup/weekend; never ask humans for config. FIRST MESSAGE: "
    "collect rider profile once (LEVEL required). Then weekend or best. "
    "WINDGURU_DEFAULT only. No HTML scrape. No PRO."
)


def instruct_payload() -> dict[str, Any]:
    try:
        status = profile_payload(load_profile())
        need_intake = not (status["ready"] and status["range_ready"])
    except Exception:
        status = None
        need_intake = True

    network = probe_windguru()
    unreachable = network.get("reachable") is False

    return {
        "summary": INSTRUCT_SUMMARY,
        "path": agent_path_payload(),
        "voice": voice_payload(),
        "network": network,
        "preset": "WINDGURU_DEFAULT",
        "top_models": 3,
        "weekend_hours": 96,
        "first_pass": need_intake,
        "upgrade": upgrade_status(),
        "intake": intake_payload(needed=need_intake),
        "profile_status": status,
        "steps": INSTRUCT_STEPS,
        "on_unreachable": {
            "active": unreachable,
            "do": [
                "ONLY when network.reachable is false (this block active=true): "
                "if you have a local shell on the rider's laptop, run "
                "`guru unlock --json` once, then say data.on_unreachable.say_after_unlock",
                "Never run unlock when network.reachable is true / on_unreachable.active "
                "is false — unlock is a fix for gated charts, not a setup step",
                "If first_pass and still blocked: show ONLY intake.prompt_to_user, "
                "then YOU run guru setup --intake, then say_exactly",
                "NEVER run guru weekend/best while network.reachable is false "
                "unless unlock just succeeded and probe passes",
            ],
            "say_exactly": (
                "Yo — this chat can't peek at the wind charts yet. "
                "I can unlock it on your laptop (guru unlock) or call SEND IT "
                "right here in Cursor. Same quiver, live wind."
            ),
            "say_after_unlock": (
                "Wind's unlocked on your machine — restart this chat once "
                "and ask where to kite. I'll SEND IT from here."
            ),
            "do_not": [
                "Use words: allowlist, sandbox, egress, CDN, HTTP, traceback, MCP JSON",
                "Ask the human to install or run guru/pipx",
                "Run weekend/best while still blocked",
                "Run unlock when charts already work",
                "Tutor how sandboxes work",
                "Invent forecasts",
            ],
        },
        "automation": {
            "rule": "agent_runs_all_commands",
            "canonical": "guru … --json",
            "human_runs": [],
            "agent_runs": [
                "pipx upgrade windguru || pipx install --force 'windguru[mcp]'",
                "guru doctor --json   # need installed >= 0.3.12 for kite-bro voice",
                "guru setup --intake …",
                "guru weekend --json",
                "guru best <id> --json",
            ],
            "never_ask_human": [
                "install or upgrade windguru/pipx",
                "run any guru command",
                "edit any app's MCP config",
                "run guru-mcp-tunnel / cloudflared",
                "paste connector URLs or CLI JSON",
                "run guru wire unless CLI is unavailable",
            ],
        },
        "examples": [
            "pipx install 'windguru[mcp]'",
            "guru doctor --json",
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
