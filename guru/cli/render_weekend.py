"""Rich tables for where / weekend scan reports."""

from __future__ import annotations

__all__ = ("print_weekend",)

from rich.table import Table

from guru.cli.console import console
from guru.models.advice import WeekendReport
from guru.rider.voice import call_label


def print_weekend(report: WeekendReport) -> None:
    title = "Weekend" if report.mode == "weekend" else "Where"
    top_n = max(int(report.top_models or 3), 1)
    console.print(
        f"[bold]{title}[/bold] · {call_label(report.verdict)} · {report.summary}"
    )
    if report.mode == "weekend" and report.weekend_start and report.weekend_end:
        console.print(
            f"[dim]Fri eve -> Sun · {report.weekend_start[:10]} .. "
            f"{report.weekend_end[:10]}[/dim]"
        )
    if report.uncertain:
        console.print(
            "[yellow]Coverage thin: high-% WINDGURU_DEFAULT models may not "
            "reach this weekend yet -- early look only[/yellow]"
        )
    if report.range_label:
        console.print(f"Range: {report.range_label}")
    console.print(
        f"[dim]horizon ~{report.hours}h · top {top_n} models[/dim]"
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
                f"{s.start[11:16]}-{s.end[11:16]}",
                f"{wind} / {gust}",
                s.rating or "-",
                kite,
                f"{s.model_agree}/{top_n}",
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
            f"{s.model_agree}/{top_n}",
            s.verdict,
            s.summary[:50],
        )
    console.print(table)
