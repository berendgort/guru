"""MCP tools: profile, unlock, and wire."""

from __future__ import annotations

__all__ = (
    "register",
)

from collections.abc import Callable
from typing import Any

from fastmcp import FastMCP

from guru.rider.instruct import instruct_payload
from guru.rider.profile_store import profile_payload, update_profile


def register(
    mcp: FastMCP,
    *,
    catch: tuple[type[BaseException], ...],
    ok: Callable[[Any], dict[str, Any]],
    err: Callable[[BaseException], dict[str, Any]],
) -> None:
    @mcp.tool(name="instruct")
    def instruct() -> dict[str, Any]:
        """Agent recipe: first-pass intake → where_spots / weekend_spots / best_forecast."""
        return ok(instruct_payload())

    @mcp.tool(name="setup_profile")
    def setup_profile_tool(
        intake: str | None = None,
        sport: str | None = None,
        weight_kg: float | None = None,
        level: str | None = None,
        kites_m2: list[float] | None = None,
        boards: list[str] | None = None,
        wetsuits: list[str] | None = None,
        home_spots: list[int] | None = None,
        home_lat: float | None = None,
        home_lon: float | None = None,
        drive_km: float | None = None,
        range_label: str | None = None,
        session_hours: float | None = None,
    ) -> dict[str, Any]:
        """Write rider profile. Prefer ``intake`` one-liner from first-pass user reply."""
        from guru.rider.intake import parse_intake_text

        try:
            parsed: dict[str, Any] = parse_intake_text(intake) if intake else {}
            profile = update_profile(
                sport=sport if sport is not None else parsed.get("sport"),
                weight_kg=weight_kg if weight_kg is not None else parsed.get("weight_kg"),
                level=level if level is not None else parsed.get("level"),
                kites_m2=kites_m2 if kites_m2 is not None else parsed.get("kites_m2"),
                boards=boards if boards is not None else parsed.get("boards"),
                wetsuits=wetsuits if wetsuits is not None else parsed.get("wetsuits"),
                home_spots=home_spots,
                home_lat=home_lat if home_lat is not None else parsed.get("home_lat"),
                home_lon=home_lon if home_lon is not None else parsed.get("home_lon"),
                drive_km=drive_km if drive_km is not None else parsed.get("drive_km"),
                range_label=(
                    range_label if range_label is not None else parsed.get("range_label")
                ),
                session_hours=(
                    session_hours
                    if session_hours is not None
                    else parsed.get("session_hours")
                ),
            )
            return ok(profile_payload(profile))
        except catch as exc:
            return err(exc)

    @mcp.tool(name="get_profile")
    def get_profile_tool() -> dict[str, Any]:
        """Return rider profile + missing fields / setup hint."""
        try:
            return ok(profile_payload())
        except catch as exc:
            return err(exc)

    @mcp.tool(name="unlock")
    def unlock_tool(force: bool = False) -> dict[str, Any]:
        """Open Windguru for Claude + ChatGPT Work/Codex on this laptop.

        Call ONLY when network.reachable is false / charts are gated. Skips when
        already reachable unless force=true. Returns rider_facing (user-visible
        UX copy) -- not a system prompt.
        """
        from guru.core.unlock import unlock_wind_charts

        try:
            return ok(unlock_wind_charts(force=force))
        except catch as exc:
            return err(exc)

    @mcp.tool(name="unlock_claude")
    def unlock_claude_tool(force: bool = False) -> dict[str, Any]:
        """Alias for unlock -- same Claude + ChatGPT Work/Codex allowlist fix."""
        return unlock_tool(force=force)

    @mcp.tool(name="wire_mcp")
    def wire_mcp_tool(status_only: bool = False) -> dict[str, Any]:
        """Wire local STDIO guru-mcp into common MCP configs.

        Call ONLY when necessary: no working shell ``guru`` AND the host needs
        local STDIO MCP with guru missing. Default path is CLI -- do not wire
        every session. Prefer status_only=true to inspect first.
        """
        from guru.core.wire import wire_all, wire_status

        try:
            return ok(wire_status() if status_only else wire_all())
        except catch as exc:
            return err(exc)
