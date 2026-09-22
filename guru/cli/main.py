"""Typer CLI -- agent-friendly Windguru client (thin shell)."""

from __future__ import annotations

import click
import typer
from typer.core import TyperGroup

from guru.cli import cmd_forecast, cmd_ops, cmd_rider
from guru.cli.banner import print_banner

__all__ = ("app", "cli")


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
        "Kite bro who codes -- spot + gear calls for riders and agents. "
        "Named like Windguru (Wind + Guru): less Tune tabs, more water time. "
        "Happy path: setup (intake) -> `guru weekend` or `guru best <spot>`. "
        "Run `guru instruct --json` for the recipe."
    ),
    no_args_is_help=True,
    add_completion=False,
)

cmd_ops.register(app)
cmd_rider.register(app)
cmd_forecast.register(app)


def cli() -> None:
    app()


if __name__ == "__main__":
    cli()
