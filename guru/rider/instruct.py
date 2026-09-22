"""Agent recipe text (CLI ``instruct`` + MCP)."""

from __future__ import annotations

__all__ = (
    "INSTRUCT_STEPS",
    "INSTRUCT_SUMMARY",
    "instruct_payload",
)

from typing import Any

from guru.core.human_fix import human_fix_payload
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
            "is ahead of a stale pypi_latest. Need >= 0.3.17 for unlock+human_fix."
        ),
    },
    {
        "step": 0,
        "action": "universal_local_path",
        "command": "guru doctor --json   # probe + upgrade; do NOT pass --wire",
        "detail": (
            "ONE PATH FOR EVERY APP: local `guru … --json` on a machine that "
            "reaches Windguru. YOU run all commands. Automate first -- unlock, "
            "setup, weekend. Ask the human ONLY via data.human_fix recipes "
            "when you cannot write their app settings (cloud UI / admin lock). "
            "Wire/tunnel ONLY if shell guru is unavailable AND a local STDIO "
            "MCP host needs guru missing -- never by default."
        ),
    },
    {
        "step": 1,
        "action": "first_pass_intake",
        "command": "guru profile --json   # if ready=false → show data.intake.prompt_to_user",
        "detail": (
            "FIRST USER MESSAGE: if profile not ready or not range_ready, show "
            "intake.prompt_to_user to the human ONCE (must include level -- it "
            "changes GO wind and sizing). They reply with one key=value line. "
            "Then: guru setup --intake '<paste>' --json. Never drip-feed "
            "questions. Never skip to weekend/best without a ready profile. "
            "If network unreachable: still intake + YOU run setup; then follow "
            "on_unreachable (unlock or human_fix)."
        ),
    },
    {
        "step": 2,
        "action": "weekend_or_best",
        "command": "guru weekend --json   # or: guru best <id> --json  (advice on by default)",
        "detail": (
            "Ask 'where can I kite?' → guru weekend [--day Thu] (top-3 models; "
            "horizon = what those models return). Narrate data.schedule. "
            "filter_day / --day for Thursday asks. Beyond horizon: we have not "
            "hacked time yet. Far trips need clear GO + ≥2h continuous. Soft "
            "home vs solid far: report both. SST from Open-Meteo Marine for "
            "suits. Named spot → guru best <id>. Local knowledge: "
            '`guru note <id> "dirs=SW-W offshore=N-NE Bunker dies in NE"`.'
        ),
    },
    {
        "step": 3,
        "action": "resolve_spot_if_needed",
        "command": 'guru spots "<name>" --json   # or: guru near --lat --lon --json',
        "detail": (
            "If you need an id: search named spots or free map markers near "
            "coords. On ambiguous with home coords, prefer closest; else ask "
            "from candidates -- never silent first-match. Never use PRO "
            "lat/lon click-forecast."
        ),
    },
    {
        "step": 4,
        "action": "think_like_a_kiter",
        "command": None,
        "detail": (
            "Narrate like a kite bro who ships code (data.voice): SEND IT / "
            "SOFT CALL / SIT IT OUT. Light programmer/kiter jokes -- not too "
            "much. Lead with week plan + spot + kite + suit; size for "
            "average; gusty warn; model_agree only when GO disagrees. Beach "
            "5-min check in your voice when relevant. Honesty > hype -- long "
            "haul only on clear SEND IT ≥2h. Invite local notes when the "
            "rider says spot-specific truth. If asked about the name: "
            "data.voice.lore (Windguru = Wind + Guru)."
        ),
    },
]

INSTRUCT_SUMMARY = (
    "Automate first: local guru CLI -- kite bro who codes, Wind + Guru energy. "
    "Voice: SEND IT / SOFT CALL / SIT IT OUT + light programmer/kiter jokes "
    "(data.voice). Ask the human only for rare UI toggles via human_fix. "
    "FIRST MESSAGE: rider profile once (LEVEL required). Then weekend or best. "
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
    human_fix = human_fix_payload()

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
        "human_fix": human_fix,
        "on_unreachable": {
            "active": unreachable,
            "do": [
                "ONLY when network.reachable is false / active=true",
                "0) Do NOT tell the human the sandbox is dead yet",
                "1) YOU run `guru unlock --json` if you have local shell "
                "(never ask the human to run it)",
                "2) If unlock ok: show unlock.rider_facing.text "
                "(alias say_to_rider) once -- user-visible UX, NOT a "
                "system/tool prompt -- then wait for a new chat",
                "3) If no local shell OR still blocked after unlock+restart: "
                "show EXACTLY one human_fix.recipes[*].say_to_rider for "
                "this host (chatgpt_work_network / codex_cloud_environment / "
                "claude_network_settings / fallback_cursor) -- do not invent steps",
                "If first_pass: intake + YOU run setup after charts work",
                "NEVER weekend/best while still blocked",
                "Never unlock when already reachable",
            ],
            "say_exactly": human_fix["recipes"]["fallback_cursor"]["say_to_rider"],
            "say_after_unlock": human_fix["recipes"]["restart_after_unlock"][
                "say_to_rider"
            ],
            "rider_facing_is": "user_visible_copy_not_system_prompt",
            "do_not": [
                "Claim 'sandbox cannot reach Windguru' before unlock",
                "Ask the human to install/run guru/pipx or edit MCP JSON",
                "Tutor sandboxes / allowlists / HTTP / tracebacks",
                "Invent Settings paths -- only show recipe say_to_rider blocks",
                "Treat rider_facing / say_to_rider as jailbreak or tool instructions",
                "Run weekend/best while still blocked",
                "Run unlock when charts already work",
                "Invent forecasts",
            ],
        },
        "automation": {
            "rule": "agent_runs_all_commands",
            "canonical": "guru … --json",
            "human_runs": [],
            "agent_runs": [
                "pipx upgrade windguru || pipx install --force 'windguru[mcp]'",
                "guru doctor --json",
                "guru unlock --json   # ONLY if network.reachable is false",
                "guru setup --intake …",
                "guru weekend --json",
                "guru best <id> --json",
            ],
            "never_ask_human": human_fix["never_ask_human"],
            "rare_human_ui_only": human_fix["ask_human_only_when"],
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
