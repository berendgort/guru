"""Rich human-readable tables."""

from __future__ import annotations

from rich.table import Table

from guru.cli.console import console
from guru.models.blend import BestForecast
from guru.models.forecast import Forecast, Spot, wind_dir_cardinal


def print_spots_table(spots: list[Spot], *, title: str) -> None:
    table = Table(title=title)
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Country")
    table.add_column("Nick")
    for s in spots:
        table.add_row(str(s.id), s.name, s.country or "", s.nickname or "")
    console.print(table)


def print_near_table(spots: list[Spot], *, lat: float, lon: float, radius: float) -> None:
    table = Table(title=f"Spots within {radius:g} km of {lat:g},{lon:g}")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Lat")
    table.add_column("Lon")
    for s in spots:
        lat_s = f"{s.lat:.4f}" if s.lat is not None else ""
        lon_s = f"{s.lon:.4f}" if s.lon is not None else ""
        table.add_row(str(s.id), s.name, lat_s, lon_s)
    console.print(table)


def print_models_table(rows: list[dict[str, object]]) -> None:
    table = Table(title="Models")
    table.add_column("ID")
    table.add_column("Primary")
    table.add_column("Aliases")
    for row in rows:
        aliases = row.get("aliases") or []
        alias_s = ", ".join(str(a) for a in aliases)  # type: ignore[arg-type]
        table.add_row(str(row["id"]), str(row["primary"]), alias_s)
    console.print(table)


def print_best(best: BestForecast) -> None:
    console.print(
        f"[bold]{best.spot.name}[/bold] · preset {best.preset} · top {len(best.models)}"
    )
    table = Table(title="WINDGURU DEFAULT weights")
    table.add_column("#")
    table.add_column("Model")
    table.add_column("ID")
    table.add_column("%", justify="right")
    for m in best.models:
        table.add_row(str(m.rank), m.name, str(m.id_model), f"{m.weight_pct:.1f}")
    console.print(table)
    for fc in best.forecasts:
        print_forecast(fc)


def print_forecast(fc: Forecast) -> None:
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


def _fmt(v: float | None, digits: int) -> str:
    return "-" if v is None else f"{v:.{digits}f}"
