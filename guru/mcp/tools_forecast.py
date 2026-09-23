"""MCP tools: where scan, spots, and forecasts."""

from __future__ import annotations

__all__ = ("register",)

from collections.abc import Callable
from typing import Any

from fastmcp import FastMCP

from guru.core.envelope import dump_model
from guru.models.aliases import list_models
from guru.rider.advice import advise_forecast
from guru.rider.profile_store import load_profile
from guru.rider.weekend import DEFAULT_WHERE_HOURS, scan_weekend
from guru.search.blend import get_best_forecast
from guru.search.forecast import get_forecast
from guru.search.near import spots_near
from guru.search.spots import resolve_spot, search_spots


def register(
    mcp: FastMCP,
    *,
    catch: tuple[type[BaseException], ...],
    ok: Callable[[Any], dict[str, Any]],
    err: Callable[[BaseException], dict[str, Any]],
) -> None:
    def _where(
        hours: int,
        limit: int,
        top: int,
        filter_day: str | None,
        weekend: bool,
    ) -> dict[str, Any]:
        day = filter_day or ("weekend" if weekend else None)
        try:
            return ok(
                dump_model(
                    scan_weekend(
                        load_profile(),
                        hours=hours,
                        limit_spots=limit,
                        top_models=top,
                        filter_day=day,
                    )
                )
            )
        except catch as exc:
            return err(exc)

    @mcp.tool(name="where_spots")
    def where_spots_tool(
        hours: int = DEFAULT_WHERE_HOURS,
        limit: int = 8,
        top: int = 3,
        filter_day: str | None = None,
        weekend: bool = False,
    ) -> dict[str, Any]:
        """Where can I kite in the next ~3 days? Schedule + ranked spots."""
        return _where(hours, limit, top, filter_day, weekend)

    @mcp.tool(name="weekend_spots")
    def weekend_spots_tool(
        hours: int = DEFAULT_WHERE_HOURS,
        limit: int = 8,
        top: int = 3,
        filter_day: str | None = None,
        weekend: bool = False,
    ) -> dict[str, Any]:
        """Alias for where_spots (next ~3 days; set weekend=true for Sat/Sun)."""
        return _where(hours, limit, top, filter_day, weekend)

    @mcp.tool(name="search_spots")
    def search_spots_tool(query: str, limit: int = 20) -> dict[str, Any]:
        """Search named Windguru spots."""
        try:
            return ok([dump_model(s) for s in search_spots(query, limit=limit)])
        except catch as exc:
            return err(exc)

    @mcp.tool(name="near_spots")
    def near_spots_tool(
        lat: float, lon: float, radius_km: float = 50.0, limit: int = 20
    ) -> dict[str, Any]:
        """Named spots near coordinates (free map markers)."""
        try:
            return ok(
                [
                    dump_model(s)
                    for s in spots_near(lat, lon, radius_km=radius_km, limit=limit)
                ]
            )
        except catch as exc:
            return err(exc)

    @mcp.tool(name="resolve_spot")
    def resolve_spot_tool(spot: str, pick: int | None = None) -> dict[str, Any]:
        """Resolve a name or id to a spot (ambiguous → error + candidates)."""
        try:
            return ok(dump_model(resolve_spot(spot, pick=pick)))
        except catch as exc:
            return err(exc)

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
            return ok(payload)
        except catch as exc:
            return err(exc)

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
            return ok(dump_model(get_forecast(resolved.id, model=model, hours=hours)))
        except catch as exc:
            return err(exc)

    @mcp.tool(name="list_models")
    def list_models_tool() -> dict[str, Any]:
        """Known model aliases."""
        return ok(list_models())
