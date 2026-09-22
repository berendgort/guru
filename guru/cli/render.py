"""Rich human-readable tables."""

from __future__ import annotations

from rich.table import Table

from guru.cli.console import console
from guru.models.blend import BestForecast
from guru.models.forecast import Forecast, Spot, wind_dir_cardinal
from guru.models.profile import AdviceReport, RiderProfile, WeekendReport


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


def print_best(best: BestForecast, advice: AdviceReport | None = None) -> None:
    console.print(
        f"[bold]{best.spot.name}[/bold] · preset {best.preset} · top {len(best.models)}"
    )
    if advice is not None:
        print_advice(advice)
        # Lead with the call; show top model hours only (raw dump is --no-advise)
        if best.forecasts:
            print_forecast(best.forecasts[0])
        return
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


def print_advice(advice: AdviceReport) -> None:
    console.print(f"[bold]Advice[/bold] · {advice.verdict} · {advice.summary}")
    if advice.missing_profile:
        console.print(f"[yellow]Missing profile: {', '.join(advice.missing_profile)}[/yellow]")
        return
    if advice.checklist:
        for item in advice.checklist[:4]:
            console.print(f"  · {item}")
    if not advice.windows:
        return
    table = Table(title="Ride windows")
    table.add_column("UTC")
    table.add_column("kt", justify="right")
    table.add_column("Gust", justify="right")
    table.add_column("WG")
    table.add_column("Quality")
    table.add_column("Kite")
    table.add_column("Suit")
    table.add_column("Verdict")
    table.add_column("Note")
    for w in advice.windows:
        kite = ""
        if w.owned_kite_m2 is not None:
            kite = f"{w.owned_kite_m2:g}"
            if w.kite_m2 is not None:
                kite += f" (~{w.kite_m2:g})"
        elif w.kite_m2 is not None:
            kite = f"~{w.kite_m2:g}"
        suit = w.owned_wetsuit or w.wetsuit or "-"
        if w.accessories:
            suit += f" +{','.join(w.accessories[:2])}"
        table.add_row(
            f"{w.start}→{w.end}",
            f"{w.wind_kn:g}",
            "-" if w.gust_kn is None else f"{w.gust_kn:g}",
            w.rating or "—",
            w.wind_quality or "-",
            kite,
            suit,
            w.verdict,
            w.note,
        )
    console.print(table)


def print_weekend(report: WeekendReport) -> None:
    console.print(f"[bold]Weekend[/bold] · {report.verdict} · {report.summary}")
    if report.range_label:
        console.print(f"Range: {report.range_label}")
    console.print(
        f"[dim]horizon ~{report.hours}h · top {report.top_models} models[/dim]"
    )
    if report.missing_profile:
        console.print(
            f"[yellow]Missing: {', '.join(report.missing_profile)}[/yellow]"
        )
        return
    for item in report.thinking[:3]:
        console.print(f"  · {item}")
    if report.schedule:
        table = Table(title="When to kite (schedule)")
        table.add_column("Day")
        table.add_column("Spot")
        table.add_column("km", justify="right")
        table.add_column("Window")
        table.add_column("kt / gust")
        table.add_column("WG")
        table.add_column("Kite")
        table.add_column("Agree")
        table.add_column("Verdict")
        for s in report.schedule:
            gust = "-" if s.gust_kn is None else f"{s.gust_kn:g}"
            wind = "-" if s.wind_kn is None else f"{s.wind_kn:g}"
            kite = "-" if s.owned_kite_m2 is None else f"{s.owned_kite_m2:g}"
            table.add_row(
                f"{s.weekday} {s.day[5:]}",
                s.name[:28],
                "-" if s.drive_km is None else f"{s.drive_km:g}",
                f"{s.start[11:16]}–{s.end[11:16]}",
                f"{wind} / {gust}",
                s.rating or "—",
                kite,
                f"{s.model_agree}/3",
                s.verdict,
            )
        console.print(table)
    if not report.spots:
        return
    table = Table(title="Spots in drive range")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("km", justify="right")
    table.add_column("Agree")
    table.add_column("Verdict")
    table.add_column("Summary")
    for s in report.spots:
        table.add_row(
            str(s.spot_id),
            s.name,
            "-" if s.drive_km is None else f"{s.drive_km:g}",
            f"{s.model_agree}/3",
            s.verdict,
            s.summary[:50],
        )
    console.print(table)


def print_profile(
    profile: RiderProfile,
    *,
    path: str,
    ready: bool,
    missing: list[str],
    range_ready: bool = False,
    missing_range: list[str] | None = None,
) -> None:
    console.print(
        f"Profile [cyan]{path}[/cyan] · ready={ready} · range_ready={range_ready}"
    )
    console.print(f"  sport={profile.sport.value if profile.sport else '-'}")
    console.print(f"  weight_kg={profile.weight_kg if profile.weight_kg is not None else '-'}")
    console.print(f"  level={profile.level.value if profile.level else '-'}")
    console.print(f"  session_hours={profile.session_hours}")
    console.print(f"  kites_m2={profile.kites_m2 or '-'}")
    console.print(f"  boards={profile.boards or '-'}")
    console.print(f"  wetsuits={profile.wetsuits or '-'}")
    home = "-"
    if profile.home_lat is not None and profile.home_lon is not None:
        home = f"{profile.home_lat:g},{profile.home_lon:g}"
    console.print(f"  home={home} drive_km={profile.drive_km or '-'}")
    console.print(f"  range_label={profile.range_label or '-'}")
    if missing:
        console.print(f"[yellow]Missing: {', '.join(missing)}[/yellow]")
    if missing_range:
        console.print(f"[yellow]Missing range: {', '.join(missing_range)}[/yellow]")


def print_forecast(fc: Forecast) -> None:
    title = f"{fc.spot.name} · {fc.model} ({fc.model_id})"
    if fc.init:
        title += f" · init {fc.init.strftime('%Y-%m-%d %HZ')}"
    table = Table(title=title)
    table.add_column("UTC", style="dim")
    table.add_column("kt", justify="right")
    table.add_column("Gust", justify="right")
    table.add_column("WG")
    table.add_column("Dir")
    table.add_column("°C", justify="right")
    table.add_column("mm", justify="right")
    for row in fc.hours:
        table.add_row(
            row.time.strftime("%a %d %H:%M"),
            _fmt(row.wind_kn, 1),
            _fmt(row.gust_kn, 1),
            row.rating or "—",
            f"{wind_dir_cardinal(row.wind_dir_deg)} {_fmt(row.wind_dir_deg, 0)}".strip(),
            _fmt(row.temp_c, 1),
            _fmt(row.precip_mm, 1),
        )
    console.print(table)


def _fmt(v: float | None, digits: int) -> str:
    return "-" if v is None else f"{v:.{digits}f}"
