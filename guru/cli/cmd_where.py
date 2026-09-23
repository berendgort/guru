"""CLI: where / weekend (next ~3 days spot schedule)."""

from __future__ import annotations

import typer

from guru.cli.catch import CATCH
from guru.cli.errors import fail, print_ok
from guru.cli.render import print_weekend
from guru.core.envelope import dump_model
from guru.rider.profile_store import load_profile
from guru.rider.weekend import DEFAULT_WHERE_HOURS, scan_weekend
from guru.search.exceptions import GuruError

__all__ = ("register",)


def _run_where(
    *,
    hours: int,
    limit: int,
    top: int,
    day: str | None,
    weekend_only: bool,
    as_json: bool,
) -> None:
    from guru.core.path import probe_windguru

    filter_day = day
    if weekend_only and not day:
        filter_day = "weekend"
    try:
        net = probe_windguru()
        if net.get("reachable") is False:
            raise GuruError(
                net.get("error")
                or "Windguru unreachable -- use a local agent host."
            )
        report = scan_weekend(
            load_profile(),
            hours=hours,
            limit_spots=limit,
            top_models=top,
            filter_day=filter_day,
        )
    except CATCH as exc:
        fail(exc, as_json=as_json)
        return
    if as_json:
        print_ok(dump_model(report))
        return
    print_weekend(report)


def register(app: typer.Typer) -> None:
    @app.command("where")
    def where_cmd(
        hours: int = typer.Option(
            DEFAULT_WHERE_HOURS,
            "--hours",
            "-H",
            help="Horizon in forecast steps (~3 days)",
        ),
        limit: int = typer.Option(8, "--limit", "-n", help="Max spots to scan"),
        top: int = typer.Option(3, "--top", help="WINDGURU_DEFAULT models"),
        day: str | None = typer.Option(
            None, "--day", help="Filter: Thu / YYYY-MM-DD / weekend"
        ),
        weekend_only: bool = typer.Option(
            False, "--weekend", help="Only Sat/Sun slots"
        ),
        as_json: bool = typer.Option(False, "--json"),
    ) -> None:
        """Where can I kite in the next ~3 days? Schedule + ranked spots."""
        _run_where(
            hours=hours,
            limit=limit,
            top=top,
            day=day,
            weekend_only=weekend_only,
            as_json=as_json,
        )

    @app.command("weekend")
    def weekend_cmd(
        hours: int = typer.Option(
            DEFAULT_WHERE_HOURS,
            "--hours",
            "-H",
            help="Horizon in forecast steps (~3 days)",
        ),
        limit: int = typer.Option(8, "--limit", "-n", help="Max spots to scan"),
        top: int = typer.Option(3, "--top", help="WINDGURU_DEFAULT models"),
        day: str | None = typer.Option(
            None, "--day", help="Filter: Thu / YYYY-MM-DD / weekend"
        ),
        weekend_only: bool = typer.Option(
            False, "--weekend", help="Only Sat/Sun slots"
        ),
        as_json: bool = typer.Option(False, "--json"),
    ) -> None:
        """Alias for `guru where` (next ~3 days; pass --weekend for Sat/Sun)."""
        _run_where(
            hours=hours,
            limit=limit,
            top=top,
            day=day,
            weekend_only=weekend_only,
            as_json=as_json,
        )
