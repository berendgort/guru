"""Typer CLI — agent-friendly Windguru client."""

from __future__ import annotations

import os

import click
import typer
from typer.core import TyperGroup

from guru import __version__
from guru.cli.banner import print_banner
from guru.cli.console import console
from guru.cli.errors import fail, print_ok
from guru.cli.render import (
    print_best,
    print_forecast,
    print_models_table,
    print_near_table,
    print_profile,
    print_spots_table,
    print_weekend,
)
from guru.core.envelope import ERROR_SCHEMA, dump_model
from guru.core.instruct import instruct_payload
from guru.models.aliases import list_models
from guru.rider.advice import advise_forecast
from guru.rider.profile_store import (
    load_profile,
    parse_float_list,
    parse_str_list,
    profile_payload,
    update_profile,
)
from guru.rider.weekend import scan_weekend
from guru.search.blend import get_best_forecast
from guru.search.exceptions import GuruError
from guru.search.forecast import get_forecast
from guru.search.near import spots_near
from guru.search.spots import resolve_spot, search_spots

_CATCH = (GuruError, ValueError, OSError)


class _GuruGroup(TyperGroup):
    """Print the brand mark above ``--help``."""

    def format_help(
        self, ctx: click.Context, formatter: click.HelpFormatter
    ) -> None:
        print_banner()
        super().format_help(ctx, formatter)


app = typer.Typer(
    name="guru",
    cls=_GuruGroup,
    help=(
        "Kite spot + gear advice for riders and agents. "
        "Happy path: setup (intake) → `guru weekend` or `guru best <spot>` "
        "(advice on by default). Run `guru instruct --json` for the recipe."
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
    """Explain intake → weekend / best --advise for agents."""
    payload = instruct_payload()
    if as_json:
        print_ok(payload)
        return
    console.print(payload["summary"])
    for step in payload["steps"]:
        console.print(f"{step['step']}. {step['action']}: {step['detail']}")
        if step.get("command"):
            console.print(f"   [cyan]{step['command']}[/cyan]")


@app.command("setup")
def setup_cmd(
    intake: str | None = typer.Option(
        None,
        "--intake",
        help="One-shot key=value paste from the user (first-pass agent intake)",
    ),
    sport: str | None = typer.Option(
        None, "--sport", help="kitesurf | kitefoil | surfkite"
    ),
    weight: float | None = typer.Option(None, "--weight", help="Rider weight kg"),
    level: str | None = typer.Option(
        None, "--level", help="beginner | intermediate | advanced"
    ),
    kites: str | None = typer.Option(
        None, "--kites", help="Comma-separated kite sizes m², e.g. 7,9,12"
    ),
    boards: str | None = typer.Option(
        None, "--boards", help='Comma-separated boards, e.g. "foil 1300, TT 138"'
    ),
    wetsuits: str | None = typer.Option(
        None, "--wetsuits", help='Comma-separated suits, e.g. "3/2,4/3"'
    ),
    home_spots: str | None = typer.Option(
        None, "--home-spots", help="Comma-separated favorite spot ids"
    ),
    home_lat: float | None = typer.Option(None, "--home-lat", help="Home latitude"),
    home_lon: float | None = typer.Option(None, "--home-lon", help="Home longitude"),
    drive_km: float | None = typer.Option(
        None, "--drive-km", help="Max drive distance km (e.g. 200 for Trabucador↔Leucate)"
    ),
    range_label: str | None = typer.Option(
        None, "--range-label", help='e.g. "Trabucador → Leucate"'
    ),
    session_hours: float | None = typer.Option(
        None, "--session-hours", help="Typical session length 2–4 h (wetsuit sizing)"
    ),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """One-shot rider onboarding (flags or --intake paste — Cursor-friendly)."""
    from guru.rider.intake import parse_intake_text

    try:
        parsed: dict = {}
        if intake:
            parsed = parse_intake_text(intake)
        spots = parse_float_list(home_spots)
        home_ids = [int(x) for x in spots] if spots is not None else None
        profile = update_profile(
            sport=sport if sport is not None else parsed.get("sport"),
            weight_kg=weight if weight is not None else parsed.get("weight_kg"),
            level=level if level is not None else parsed.get("level"),
            kites_m2=(
                parse_float_list(kites)
                if kites is not None
                else parsed.get("kites_m2")
            ),
            boards=(
                parse_str_list(boards) if boards is not None else parsed.get("boards")
            ),
            wetsuits=(
                parse_str_list(wetsuits)
                if wetsuits is not None
                else parsed.get("wetsuits")
            ),
            home_spots=home_ids,
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
        payload = profile_payload(profile)
    except _CATCH as exc:
        fail(exc, as_json=as_json)
    if as_json:
        print_ok(payload)
        return
    print_profile(
        profile,
        path=str(payload["path"]),
        ready=bool(payload["ready"]),
        missing=list(payload["missing"]),
        range_ready=bool(payload["range_ready"]),
        missing_range=list(payload["missing_range"]),
    )


@app.command("profile")
def profile_cmd(
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Show rider profile + missing fields for setup."""
    try:
        payload = profile_payload()
        profile = load_profile()
    except _CATCH as exc:
        fail(exc, as_json=as_json)
    if as_json:
        print_ok(payload)
        return
    print_profile(
        profile,
        path=str(payload["path"]),
        ready=bool(payload["ready"]),
        missing=list(payload["missing"]),
        range_ready=bool(payload["range_ready"]),
        missing_range=list(payload["missing_range"]),
    )


@app.command("weekend")
def weekend_cmd(
    hours: int = typer.Option(
        96,
        "--hours",
        "-H",
        help="Forecast horizon in steps (~96 ≈ 4 days so mid-week is covered)",
    ),
    limit: int = typer.Option(8, "--limit", "-n", help="Max spots to scan"),
    top: int = typer.Option(
        3, "--top", help="WINDGURU_DEFAULT models to agree across"
    ),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Where can I kite? Rank spots + day schedule (top models, ~4-day horizon)."""
    try:
        profile = load_profile()
        report = scan_weekend(
            profile, hours=hours, limit_spots=limit, top_models=top
        )
    except _CATCH as exc:
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
    advise: bool = typer.Option(
        True,
        "--advise/--no-advise",
        help="Rider gear advice (default on — use --no-advise for raw models only)",
    ),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Spot call: WINDGURU_DEFAULT + GO/MARGINAL/NO-GO gear advice (default)."""
    from guru.rider.advice import drive_km_from_home

    try:
        resolved = resolve_spot(spot, pick=pick)
        best = get_best_forecast(resolved.id, top=top, hours=hours)
        advice = None
        if advise:
            profile = load_profile()
            top_fc = best.forecasts[0] if best.forecasts else None
            if top_fc is None:
                raise ValueError("No forecast hours to advise on")
            drive = drive_km_from_home(profile, resolved)
            advice = advise_forecast(top_fc, profile, drive_km=drive)
    except _CATCH as exc:
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
    name: str = typer.Argument(
        "forecast", help="spot | forecast | best | profile | advice | weekend | error | instruct"
    ),
) -> None:
    """Dump JSON Schema for agent payloads."""
    from guru.models.blend import BestForecast
    from guru.models.forecast import Forecast, Spot
    from guru.models.profile import AdviceReport, RiderProfile, WeekendReport

    schemas = {
        "spot": Spot.model_json_schema(),
        "forecast": Forecast.model_json_schema(),
        "best": BestForecast.model_json_schema(),
        "profile": RiderProfile.model_json_schema(),
        "advice": AdviceReport.model_json_schema(),
        "weekend": WeekendReport.model_json_schema(),
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


@app.command("wire")
def wire_cmd(
    as_json: bool = typer.Option(False, "--json"),
    status_only: bool = typer.Option(
        False, "--status", help="Check MCP wiring without writing."
    ),
) -> None:
    """Auto-wire local STDIO guru-mcp into Cursor / Claude Desktop / Claude Code.

    Only when needed: MCP-only host with no shell ``guru``, or guru MCP missing.
    Default path is CLI — do not wire every session.
    """
    from guru.core.wire import wire_all, wire_status

    try:
        payload = wire_status() if status_only else wire_all()
    except _CATCH as exc:
        fail(exc, as_json=as_json)
        return
    if as_json:
        print_ok(payload)
        return
    if not payload.get("ok", True) and not status_only:
        console.print(f"[red]{payload.get('error')}[/red] — {payload.get('hint')}")
        raise typer.Exit(1)
    if status_only:
        console.print(f"guru-mcp={payload.get('guru_mcp') or 'missing'}")
        for c in payload.get("checks") or []:
            mark = "ok" if c.get("present") else "—"
            console.print(f"  {mark} {c['target']}: {c['path']}")
        return
    console.print(f"wired guru-mcp → {payload.get('command')}")
    for w in payload.get("wired") or []:
        flag = "updated" if w.get("changed") else "unchanged"
        console.print(f"  {flag} {w.get('target')}: {w.get('path')}")
    console.print(payload.get("restart_hint") or "")


@app.command("doctor")
def doctor_cmd(
    as_json: bool = typer.Option(False, "--json"),
    wire: bool = typer.Option(
        False,
        "--wire/--no-wire",
        help="Wire local STDIO MCP adapters (OFF by default — only when needed).",
    ),
    probe: bool = typer.Option(
        True,
        "--probe/--no-probe",
        help="Probe Windguru reachability (default on).",
    ),
) -> None:
    """Env + version + network probe + optional MCP wire."""
    from guru.core.path import agent_path_payload, probe_windguru
    from guru.core.upgrade import upgrade_status
    from guru.core.wire import wire_all, wire_status

    try:
        payload = profile_payload()
    except Exception:
        payload = {"ready": False, "missing": ["profile"], "path": None}
    upgrade = upgrade_status()
    network = probe_windguru() if probe else {"skipped": True}
    wired = wire_all() if wire else wire_status()
    info = {
        "version": __version__,
        "path": agent_path_payload(),
        "network": network,
        "upgrade": upgrade,
        "GURU_TIMEOUT": os.environ.get("GURU_TIMEOUT", "30"),
        "GURU_IMPERSONATE": os.environ.get("GURU_IMPERSONATE", "chrome"),
        "models": list_models(),
        "profile": payload,
        "mcp_wire": wired,
    }
    if as_json:
        print_ok(info)
        return
    console.print(f"guru {__version__}")
    reach = network.get("reachable")
    if reach is True:
        console.print("network: Windguru reachable")
    elif reach is False:
        console.print(
            "[red]network: Windguru NOT reachable — use a local host agent[/red]"
        )
    if upgrade.get("update_available"):
        console.print(
            f"[yellow]update available: {upgrade.get('pypi_latest')} — "
            f"pipx upgrade windguru[/yellow]"
        )
    else:
        console.print(
            f"pypi={upgrade.get('pypi_latest') or '?'} · up to date"
        )
    console.print(f"GURU_TIMEOUT={info['GURU_TIMEOUT']}")
    console.print(f"GURU_IMPERSONATE={info['GURU_IMPERSONATE']}")
    console.print(f"{len(info['models'])} known model aliases")
    console.print(f"profile ready={payload.get('ready')} path={payload.get('path')}")
    if wired.get("ok"):
        console.print(f"mcp adapters → {wired.get('command')}")
    elif wire:
        console.print(f"[yellow]mcp wire: {wired.get('error')}[/yellow]")


def cli() -> None:
    app()


if __name__ == "__main__":
    cli()
