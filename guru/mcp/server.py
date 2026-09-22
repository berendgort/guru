"""Windguru MCP server — core envelope only (no CLI imports)."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from guru.core.envelope import dump_model, error_payload, success_payload
from guru.core.instruct import instruct_payload
from guru.models.aliases import list_models
from guru.rider.advice import advise_forecast
from guru.rider.profile_store import load_profile, profile_payload, update_profile
from guru.search.blend import get_best_forecast
from guru.search.exceptions import GuruError
from guru.search.forecast import get_forecast
from guru.search.near import spots_near
from guru.search.spots import resolve_spot, search_spots

mcp = FastMCP(
    "guru",
    instructions=(
        "Kite spot + gear advice. EVERY SESSION: check instruct/doctor upgrade "
        "and pipx upgrade windguru if update_available. Then get_profile; if "
        "first_pass show intake.prompt_to_user (level required). For 'where "
        "can I kite?' use weekend_spots and narrate data.schedule for the whole "
        "horizon (do not wait for 'what about Thursday?'). Named spot → "
        "best_forecast. Never scrape windguru.cz; never require PRO."
    ),
)

_CATCH = (GuruError, ValueError, OSError)


def _ok(data: Any) -> dict[str, Any]:
    return success_payload(data)


def _err(exc: BaseException) -> dict[str, Any]:
    return error_payload(exc)


@mcp.tool(name="instruct")
def instruct() -> dict[str, Any]:
    """Agent recipe: first-pass intake → weekend_spots / best_forecast."""
    return _ok(instruct_payload())


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
        return _ok(profile_payload(profile))
    except _CATCH as exc:
        return _err(exc)


@mcp.tool(name="get_profile")
def get_profile_tool() -> dict[str, Any]:
    """Return rider profile + missing fields / setup hint."""
    try:
        return _ok(profile_payload())
    except _CATCH as exc:
        return _err(exc)


@mcp.tool(name="weekend_spots")
def weekend_spots_tool(
    hours: int = 96, limit: int = 8, top: int = 3
) -> dict[str, Any]:
    """Where can I kite? Day schedule + ranked spots (top-3 models, ~4 days)."""
    from guru.rider.weekend import scan_weekend

    try:
        return _ok(
            dump_model(
                scan_weekend(
                    load_profile(),
                    hours=hours,
                    limit_spots=limit,
                    top_models=top,
                )
            )
        )
    except _CATCH as exc:
        return _err(exc)


@mcp.tool(name="search_spots")
def search_spots_tool(query: str, limit: int = 20) -> dict[str, Any]:
    """Search named Windguru spots."""
    try:
        return _ok([dump_model(s) for s in search_spots(query, limit=limit)])
    except _CATCH as exc:
        return _err(exc)


@mcp.tool(name="near_spots")
def near_spots_tool(
    lat: float, lon: float, radius_km: float = 50.0, limit: int = 20
) -> dict[str, Any]:
    """Named spots near coordinates (free map markers)."""
    try:
        return _ok(
            [dump_model(s) for s in spots_near(lat, lon, radius_km=radius_km, limit=limit)]
        )
    except _CATCH as exc:
        return _err(exc)


@mcp.tool(name="resolve_spot")
def resolve_spot_tool(spot: str, pick: int | None = None) -> dict[str, Any]:
    """Resolve a name or id to a spot (ambiguous → error + candidates)."""
    try:
        return _ok(dump_model(resolve_spot(spot, pick=pick)))
    except _CATCH as exc:
        return _err(exc)


@mcp.tool(name="best_forecast")
def best_forecast_tool(
    spot: str,
    top: int = 3,
    hours: int = 48,
    pick: int | None = None,
    advise: bool = True,
) -> dict[str, Any]:
    """WINDGURU_DEFAULT → verdict + gear advice (advise on; set false for raw)."""
    from guru.rider.advice import drive_km_from_home

    try:
        resolved = resolve_spot(spot, pick=pick)
        best = get_best_forecast(resolved.id, top=top, hours=hours)
        payload = dump_model(best)
        if advise:
            if not best.forecasts:
                raise ValueError("No forecast hours to advise on")
            profile = load_profile()
            drive = drive_km_from_home(profile, resolved)
            advice = advise_forecast(
                best.forecasts[0], profile, drive_km=drive
            )
            payload = {**payload, "advice": dump_model(advice)}
        return _ok(payload)
    except _CATCH as exc:
        return _err(exc)


@mcp.tool(name="get_forecast")
def get_forecast_tool(
    spot: str,
    model: str = "gfs",
    hours: int = 48,
    pick: int | None = None,
) -> dict[str, Any]:
    """Single-model forecast escape hatch."""
    try:
        resolved = resolve_spot(spot, pick=pick)
        return _ok(dump_model(get_forecast(resolved.id, model=model, hours=hours)))
    except _CATCH as exc:
        return _err(exc)


@mcp.tool(name="list_models")
def list_models_tool() -> dict[str, Any]:
    """Known model aliases."""
    return _ok(list_models())
