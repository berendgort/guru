"""Typer CLI — agent-friendly Windguru client (fli-style)."""

from __future__ import annotations

import os

import typer

from guru import __version__
from guru.cli.console import console
from guru.cli.errors import fail, print_ok
from guru.cli.render import (
    print_best,
    print_forecast,
    print_models_table,
    print_near_table,
    print_spots_table,
)
from guru.core.envelope import ERROR_SCHEMA, dump_model
from guru.core.instruct import instruct_payload
from guru.models.aliases import list_models
from guru.search.blend import get_best_forecast
from guru.search.exceptions import GuruError
from guru.search.forecast import get_forecast
from guru.search.near import spots_near
from guru.search.spots import resolve_spot, search_spots

_CATCH = (GuruError, ValueError, OSError)

app = typer.Typer(
    name="guru",
    help=(
        "Windguru CLI for humans and AI agents. "
        "Prefer `guru best <spot> --json` (WINDGURU_DEFAULT top 3). "
        "Run `guru instruct --json` for the agent recipe."
    ),
    no_args_is_help=True,
    add_completion=False,
)


@app.command("version")
def version_cmd(
    as_json: bool = typer.Option(False, "--json", help="Machine-readable envelope"),
) -> None:
    if as_json:
        print_ok({"version": __version__})
    else:
        console.print(__version__)


@app.command("instruct")
def instruct_cmd(
    as_json: bool = typer.Option(True, "--json/--no-json", help="JSON recipe (default on)"),
) -> None:
    """Explain the free WINDGURU_DEFAULT → top-3 workflow for agents."""
    payload = instruct_payload()
    if as_json:
        print_ok(payload)
        return
    console.print(payload["summary"])
    for step in payload["steps"]:
        console.print(f"{step['step']}. {step['action']}: {step['detail']}")
        if step.get("command"):
            console.print(f"   [cyan]{step['command']}[/cyan]")


@app.command("spots")
def spots_cmd(
    query: str = typer.Argument(..., help="Spot name search"),
    limit: int = typer.Option(20, "--limit", "-n"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Search Windguru spots by name (live API)."""
    try:
        spots = search_spots(query, limit=limit)
    except _CATCH as exc:
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
    """Named spots near a point (free map markers — not PRO click-forecast)."""
    try:
        spots = spots_near(lat, lon, radius_km=radius, limit=limit)
    except _CATCH as exc:
        fail(exc, as_json=as_json)
    if as_json:
        print_ok([dump_model(s) for s in spots])
        return
    print_near_table(spots, lat=lat, lon=lon, radius=radius)


@app.command("best")
def best_cmd(
    spot: str = typer.Argument(..., help="Spot id or unique name"),
    top: int = typer.Option(3, "--top", help="How many WINDGURU_DEFAULT models to keep"),
    hours: int = typer.Option(
        48, "--hours", "-H", help="Max forecast steps to return per model"
    ),
    pick: int | None = typer.Option(None, "--pick", help="Disambiguate by spot id"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """WINDGURU DEFAULT Tune → top models by weight → those forecasts."""
    try:
        resolved = resolve_spot(spot, pick=pick)
        best = get_best_forecast(resolved.id, top=top, hours=hours)
    except _CATCH as exc:
        fail(exc, as_json=as_json)
    if as_json:
        print_ok(dump_model(best))
        return
    print_best(best)


@app.command("forecast")
def forecast_cmd(
    spot: str = typer.Argument(..., help="Spot id or unique name"),
    model: str = typer.Option("gfs", "--model", "-m", help="Model alias or id"),
    hours: int = typer.Option(
        48, "--hours", "-H", help="Max forecast steps to return"
    ),
    pick: int | None = typer.Option(None, "--pick", help="Disambiguate by spot id"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Single-model forecast (escape hatch; prefer `guru best`)."""
    try:
        resolved = resolve_spot(spot, pick=pick)
        fc = get_forecast(resolved.id, model=model, hours=hours)
    except _CATCH as exc:
        fail(exc, as_json=as_json)
    if as_json:
        print_ok(dump_model(fc))
        return
    print_forecast(fc)


@app.command("models")
def models_cmd(
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """List known model aliases (extend from live captures)."""
    rows = list_models()
    if as_json:
        print_ok(rows)
        return
    print_models_table(rows)  # type: ignore[arg-type]


@app.command("schema")
def schema_cmd(
    name: str = typer.Argument("forecast", help="spot | forecast | best | error | instruct"),
) -> None:
    """Dump JSON Schema for agent payloads."""
    from guru.models.blend import BestForecast
    from guru.models.forecast import Forecast, Spot

    schemas = {
        "spot": Spot.model_json_schema(),
        "forecast": Forecast.model_json_schema(),
        "best": BestForecast.model_json_schema(),
        "instruct": {"type": "object", "description": "see guru instruct --json"},
        "error": ERROR_SCHEMA,
    }
    key = name.lower().strip()
    if key not in schemas:
        fail(
            ValueError(f"Unknown schema {name!r}. Choose: {', '.join(sorted(schemas))}"),
            as_json=True,
        )
    print_ok({"name": key, "schema": schemas[key]})


@app.command("doctor")
def doctor_cmd(
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Env + version sanity check (no live Windguru call)."""
    info = {
        "version": __version__,
        "GURU_TIMEOUT": os.environ.get("GURU_TIMEOUT", "30"),
        "GURU_IMPERSONATE": os.environ.get("GURU_IMPERSONATE", "chrome"),
        "models": list_models(),
    }
    if as_json:
        print_ok(info)
        return
    console.print(f"guru {__version__}")
    console.print(f"GURU_TIMEOUT={info['GURU_TIMEOUT']}")
    console.print(f"GURU_IMPERSONATE={info['GURU_IMPERSONATE']}")
    console.print(f"{len(info['models'])} known model aliases")


def cli() -> None:
    app()


if __name__ == "__main__":
    cli()
