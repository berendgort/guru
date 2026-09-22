from __future__ import annotations

import json
from typing import Optional

import typer
from rich.table import Table

from guru import __version__
from guru.cli.console import console
from guru.models.forecast import wind_dir_cardinal
from guru.search.exceptions import GuruError
from guru.search.forecast import get_forecast
from guru.search.spots import search_spots

app = typer.Typer(
    name="guru",
    help="Windguru forecast CLI (reverse-engineered, fli-style).",
    no_args_is_help=True,
    add_completion=False,
)


@app.command("version")
def version_cmd() -> None:
    console.print(__version__)


@app.command("spots")
def spots_cmd(
    query: str = typer.Argument(...),
    limit: int = typer.Option(15, "--limit", "-n"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Search Windguru spots."""
    try:
        spots = search_spots(query, limit=limit)
    except GuruError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc
    if as_json:
        console.print_json(data=[s.model_dump() for s in spots])
        return
    table = Table(title=f"Spots matching {query!r}")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Country")
    table.add_column("Nick")
    for s in spots:
        table.add_row(str(s.id), s.name, s.country or "", s.nickname or "")
    console.print(table)


@app.command("forecast")
def forecast_cmd(
    spot: str = typer.Argument(..., help="Spot id or name"),
    model: str = typer.Option("gfs", "--model", "-m"),
    hours: int = typer.Option(48, "--hours", "-H"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Show wind forecast for a spot."""
    try:
        spot_id = _resolve_spot(spot)
        fc = get_forecast(spot_id, model=model, hours=hours)
    except (GuruError, ValueError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc

    if as_json:
        console.print_json(data=json.loads(fc.model_dump_json()))
        return

    title = f"{fc.spot.name} · {fc.model} ({fc.model_id})"
    if fc.init:
        title += f" · init {fc.init.strftime('%Y-%m-%d %HZ')}"
    table = Table(title=title)
    table.add_column("UTC", style="dim")
    table.add_column("kt", justify="right")
    table.add_column("Gust", justify="right")
    table.add_column("Dir")
    table.add_column("°C", justify="right")
    table.add_column("mm", justify="right")
    for row in fc.hours:
        table.add_row(
            row.time.strftime("%a %d %H:%M"),
            _fmt(row.wind_kn, 1),
            _fmt(row.gust_kn, 1),
            f"{wind_dir_cardinal(row.wind_dir_deg)} {_fmt(row.wind_dir_deg, 0)}".strip(),
            _fmt(row.temp_c, 1),
            _fmt(row.precip_mm, 1),
        )
    console.print(table)


def _resolve_spot(spot: str) -> int:
    if spot.isdigit():
        return int(spot)
    hits = search_spots(spot, limit=5)
    if not hits:
        raise ValueError(f"No spots matching {spot!r}")
    return hits[0].id


def _fmt(v: Optional[float], digits: int) -> str:
    return "-" if v is None else f"{v:.{digits}f}"


def cli() -> None:
    app()


if __name__ == "__main__":
    cli()
