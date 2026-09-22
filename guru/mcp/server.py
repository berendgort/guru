"""Windguru MCP server — core envelope only (no CLI imports)."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from guru.core.envelope import dump_model, error_payload, success_payload
from guru.core.instruct import instruct_payload
from guru.models.aliases import list_models
from guru.search.blend import get_best_forecast
from guru.search.exceptions import GuruError
from guru.search.forecast import get_forecast
from guru.search.near import spots_near
from guru.search.spots import resolve_spot, search_spots

mcp = FastMCP(
    "guru",
    instructions=(
        "Windguru free forecast tools. Prefer best_forecast (WINDGURU_DEFAULT top 3). "
        "Call instruct first if unsure. Never scrape windguru.cz; never require PRO."
    ),
)

_CATCH = (GuruError, ValueError, OSError)


def _ok(data: Any) -> dict[str, Any]:
    return success_payload(data)


def _err(exc: BaseException) -> dict[str, Any]:
    return error_payload(exc)


@mcp.tool(name="instruct")
def instruct() -> dict[str, Any]:
    """Agent recipe: spots/near → best (WINDGURU_DEFAULT top 3)."""
    return _ok(instruct_payload())


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
) -> dict[str, Any]:
    """WINDGURU DEFAULT Tune weights → top models → forecasts.

    ``spot`` may be a numeric id or unique name (same as CLI ``guru best``).
    """
    try:
        resolved = resolve_spot(spot, pick=pick)
        best = get_best_forecast(resolved.id, top=top, hours=hours)
        return _ok(dump_model(best))
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
