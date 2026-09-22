"""CLI: version / instruct / schema / unlock / wire / doctor."""

from __future__ import annotations

import os

import typer

from guru import __version__
from guru.cli.catch import CATCH
from guru.cli.console import console
from guru.cli.errors import fail, print_ok
from guru.core.envelope import ERROR_SCHEMA
from guru.models.advice import AdviceReport, WeekendReport
from guru.models.aliases import list_models
from guru.models.profile import RiderProfile
from guru.rider.instruct import instruct_payload
from guru.rider.profile_store import profile_payload

__all__ = ("register",)


def register(app: typer.Typer) -> None:
    @app.command("version")
    def version_cmd(
        as_json: bool = typer.Option(False, "--json", help="Machine-readable envelope"),
    ) -> None:
        from guru.rider.voice import joke, tagline

        if as_json:
            print_ok(
                {
                    "version": __version__,
                    "tagline": tagline(seed=__version__),
                    "joke": joke(seed=__version__),
                }
            )
        else:
            console.print(f"{__version__}  ·  {tagline(seed=__version__)}")
            console.print(f"[dim]{joke(seed=__version__)}[/dim]")

    @app.command("instruct")
    def instruct_cmd(
        as_json: bool = typer.Option(
            True, "--json/--no-json", help="JSON recipe (default on)"
        ),
    ) -> None:
        """Explain intake -> weekend / best --advise for agents."""
        payload = instruct_payload()
        if as_json:
            print_ok(payload)
            return
        console.print(payload["summary"])
        for step in payload["steps"]:
            console.print(f"{step['step']}. {step['action']}: {step['detail']}")
            if step.get("command"):
                console.print(f"   [cyan]{step['command']}[/cyan]")

    @app.command("schema")
    def schema_cmd(
        name: str = typer.Argument(
            "forecast",
            help="spot | forecast | best | profile | advice | weekend | error | instruct",
        ),
    ) -> None:
        """Dump JSON Schema for agent payloads."""
        from guru.models.blend import BestForecast
        from guru.models.forecast import Forecast, Spot

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
                ValueError(
                    f"Unknown schema {name!r}. Choose: {', '.join(sorted(schemas))}"
                ),
                as_json=True,
            )
        print_ok({"name": key, "schema": schemas[key]})

    @app.command("unlock")
    def unlock_cmd(
        as_json: bool = typer.Option(False, "--json"),
        force: bool = typer.Option(
            False,
            "--force",
            help="Write allowlists even when Windguru is already reachable.",
        ),
    ) -> None:
        """Open Windguru for Claude + ChatGPT Work/Codex when charts are gated."""
        from guru.core.unlock import unlock_wind_charts

        try:
            payload = unlock_wind_charts(force=force)
        except CATCH as exc:
            fail(exc, as_json=as_json)
            return
        if as_json:
            print_ok(payload)
            return
        if payload.get("skipped"):
            console.print(
                "[dim]already reachable -- unlock skipped (stoke already online)[/dim]"
            )
            return
        console.print(payload.get("say_to_rider") or "unlocked")
        for key in ("claude_network", "codex_network", "network"):
            path = (payload.get(key) or {}).get("path")
            if path:
                console.print(f"[dim]{path}[/dim]")
                break

    @app.command("wire")
    def wire_cmd(
        as_json: bool = typer.Option(False, "--json"),
        status_only: bool = typer.Option(
            False, "--status", help="Check MCP wiring without writing."
        ),
    ) -> None:
        """Auto-wire local STDIO guru-mcp into Cursor / Claude Desktop / Claude Code."""
        from guru.core.wire import wire_all, wire_status

        try:
            payload = wire_status() if status_only else wire_all()
        except CATCH as exc:
            fail(exc, as_json=as_json)
            return
        if as_json:
            print_ok(payload)
            return
        if not payload.get("ok", True) and not status_only:
            console.print(
                f"[red]{payload.get('error')}[/red] -- {payload.get('hint')}"
            )
            raise typer.Exit(1)
        if status_only:
            console.print(f"guru-mcp={payload.get('guru_mcp') or 'missing'}")
            for c in payload.get("checks") or []:
                mark = "ok" if c.get("present") else "-"
                console.print(f"  {mark} {c['target']}: {c['path']}")
            return
        console.print(f"wired guru-mcp -> {payload.get('command')}")
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
            help="Wire local STDIO MCP adapters (OFF by default).",
        ),
        probe: bool = typer.Option(
            True, "--probe/--no-probe", help="Probe Windguru reachability."
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
        from guru.rider.voice import joke

        reach = network.get("reachable")
        if reach is True:
            console.print(f"network: Windguru reachable -- {joke(about='doctor_ok')}")
        elif reach is False:
            console.print(
                f"[red]network: Windguru NOT reachable[/red] -- "
                f"{joke(about='doctor_bad')}"
            )
        if upgrade.get("update_available"):
            console.print(
                f"[yellow]update available: {upgrade.get('pypi_latest')} -- "
                f"pipx upgrade windguru[/yellow]"
            )
        else:
            console.print(
                f"pypi={upgrade.get('pypi_latest') or '?'} · up to date · "
                f"{joke(about='general', seed='doctor')}"
            )
        console.print(f"GURU_TIMEOUT={info['GURU_TIMEOUT']}")
        console.print(f"GURU_IMPERSONATE={info['GURU_IMPERSONATE']}")
        console.print(f"{len(info['models'])} known model aliases")
        console.print(
            f"profile ready={payload.get('ready')} path={payload.get('path')}"
        )
        if wired.get("ok"):
            console.print(f"mcp adapters -> {wired.get('command')}")
        elif wire:
            console.print(f"[yellow]mcp wire: {wired.get('error')}[/yellow]")
