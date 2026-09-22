"""Windguru MCP server - core envelope only (no CLI imports)."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from guru.core.envelope import error_payload, success_payload
from guru.mcp import tools_forecast, tools_profile
from guru.search.exceptions import GuruError

try:
    from tenacity import RetryError as _RetryError
except ImportError:  # pragma: no cover
    _RetryError = ()  # type: ignore[misc, assignment]

mcp = FastMCP(
    "guru",
    instructions=(
        "Kite spot + gear advice in kite-bro / programmer-surfer voice "
        "(SEND IT / SOFT CALL / SIT IT OUT - see instruct.voice; jokes welcome). "
        "Windguru = Wind + Guru; this CLI is the beach sibling. "
        "ONE PATH every app: local guru CLI. "
        "EVERY SESSION: instruct/doctor without --wire. Automate everything. "
        "If network.reachable is false: run unlock once, paste say_to_rider "
        "(new chat). Still blocked / no shell: paste exactly one "
        "human_fix recipe for ChatGPT Work, Codex cloud, or Claude - "
        "never invent steps; never ask for pipx. Never unlock when already "
        "reachable. wire_mcp ONLY if shell guru unavailable. Upgrade if "
        "update_available. get_profile; if first_pass show "
        "intake.prompt_to_user (level required). 'where can I kite?' -> "
        "weekend_spots + narrate schedule in voice. Named spot -> "
        "best_forecast. Never scrape; never require PRO; never hype a soft "
        "long haul."
    ),
)

_CATCH = (GuruError, ValueError, OSError, _RetryError)


def _ok(data: Any) -> dict[str, Any]:
    return success_payload(data)


def _err(exc: BaseException) -> dict[str, Any]:
    return error_payload(exc)


tools_profile.register(mcp, catch=_CATCH, ok=_ok, err=_err)
tools_forecast.register(mcp, catch=_CATCH, ok=_ok, err=_err)

__all__ = ("mcp",)
