"""CLI: weekend / spots / near / best / forecast / models."""

from __future__ import annotations

import typer

from guru.cli.catch import CATCH
from guru.cli.errors import fail, print_ok
from guru.cli.render import (
    print_best,
    print_forecast,
    print_models_table,
    print_near_table,
    print_spots_table,
    print_weekend,
)
from guru.core.envelope import dump_model
from guru.models.aliases import list_models
from guru.rider.advice import advise_forecast
from guru.rider.profile_store import load_profile
from guru.rider.weekend import scan_weekend
from guru.search.blend import get_best_forecast
from guru.search.exceptions import GuruError
from guru.search.forecast import get_forecast
from guru.search.near import spots_near
from guru.search.spots import resolve_spot, search_spots

__all__ = ("register",)


def register(app: typer.Typer) -> None:
    @app.command("weekend")
    def weekend_cmd(
        hours: int = typer.Option(96, "--hours", "-H", help="Forecast horizon steps"),
        limit: int = typer.Option(8, "--limit", "-n", help="Max spots to scan"),
        top: int = typer.Option(3, "--top", help="WINDGURU_DEFAULT models"),
        day: str | None = typer.Option(
            None, "--day", help="Filter: Thu / Thursday / YYYY-MM-DD"
        ),
        as_json: bool = typer.Option(False, "--json"),
    ) -> None:
        """Where can I kite? Rank spots + day schedule."""
        from guru.core.path import probe_windguru

        try:
            net = probe_windguru()
            if net.get("reachable") is False:
                raise GuruError(
                    net.get("fix")
                    or "Windguru unreachable -- use a local agent host."
                )
            profile = load_profile()
            report = scan_weekend(
                profile,
                hours=hours,
                limit_spots=limit,
                top_models=top,
                filter_day=day,
            )
        except CATCH as exc:
            fail(exc, as_json=as_json)
        if as_json:
            print_ok(dump_model(report))
            return
        print_weekend(report)

    @app.command("spots")
    def spots_cmd(
        query: str = typer.Argument(..., help="Spot name search"),
        limit: int = typer.Option(20, "--limit", "-n"),
        as_json: bool = typer.Option(False, "--json"),
    ) -> None:
        """Search Windguru spots by name (live API)."""
        try:
            spots = search_spots(query, limit=limit)
        except CATCH as exc:
            fail(exc, as_json=as_json)
        if as_json:
            print_ok([dump_model(s) for s in spots])
            return
        print_spots_table(spots, title=f"Spots matching {query!r}")

    @app.command("near")
    def near_cmd(
        lat: float = typer.Option(..., "--lat", help="Latitude"),
        lon: float = typer.Option(..., "--lon", help="Longitude"),
        radius: float = typer.Option(50.0, "--radius", help="Search radius km"),
        limit: int = typer.Option(20, "--limit", "-n"),
        as_json: bool = typer.Option(False, "--json"),
    ) -> None:
        """Named spots near a point (free map markers, not PRO)."""
        try:
            spots = spots_near(lat, lon, radius_km=radius, limit=limit)
        except CATCH as exc:
            fail(exc, as_json=as_json)
        if as_json:
            print_ok([dump_model(s) for s in spots])
            return
        print_near_table(spots, lat=lat, lon=lon, radius=radius)

    @app.command("best")
    def best_cmd(
        spot: str = typer.Argument(..., help="Spot id or unique name"),
        top: int = typer.Option(3, "--top", help="WINDGURU_DEFAULT models to keep"),
        hours: int = typer.Option(48, "--hours", "-H", help="Max forecast steps"),
        pick: int | None = typer.Option(None, "--pick", help="Disambiguate by spot id"),
        advise: bool = typer.Option(
            True,
            "--advise/--no-advise",
            help="Rider gear advice (default on)",
        ),
        as_json: bool = typer.Option(False, "--json"),
    ) -> None:
        """Spot call: WINDGURU_DEFAULT + GO/MARGINAL/NO-GO gear advice."""
        from guru.rider.advice import drive_km_from_home

        try:
            profile = load_profile()
            resolved = resolve_spot(
                spot,
                pick=pick,
                prefer_lat=profile.home_lat,
                prefer_lon=profile.home_lon,
            )
            best = get_best_forecast(resolved.id, top=top, hours=hours)
            advice = None
            if advise:
                top_fc = best.forecasts[0] if best.forecasts else None
                if top_fc is None:
                    raise ValueError("No forecast hours to advise on")
                drive = drive_km_from_home(profile, resolved)
                advice = advise_forecast(top_fc, profile, drive_km=drive)
        except CATCH as exc:
            fail(exc, as_json=as_json)
        if as_json:
            payload = dump_model(best)
            if advice is not None:
                payload = {**payload, "advice": dump_model(advice)}
            print_ok(payload)
            return
        print_best(best, advice=advice)

    @app.command("forecast")
    def forecast_cmd(
        spot: str = typer.Argument(..., help="Spot id or unique name"),
        model: str = typer.Option("gfs", "--model", "-m", help="Model alias or id"),
        hours: int = typer.Option(48, "--hours", "-H", help="Max forecast steps"),
        pick: int | None = typer.Option(None, "--pick", help="Disambiguate by spot id"),
        as_json: bool = typer.Option(False, "--json"),
    ) -> None:
        """Single-model forecast (escape hatch; prefer `guru best`)."""
        try:
            resolved = resolve_spot(spot, pick=pick)
            fc = get_forecast(resolved.id, model=model, hours=hours)
        except CATCH as exc:
            fail(exc, as_json=as_json)
        if as_json:
            print_ok(dump_model(fc))
            return
        print_forecast(fc)

    @app.command("models")
    def models_cmd(as_json: bool = typer.Option(False, "--json")) -> None:
        """List known model aliases (extend from live captures)."""
        rows = list_models()
        if as_json:
            print_ok(rows)
            return
        print_models_table(rows)  # type: ignore[arg-type]
