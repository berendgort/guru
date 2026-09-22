"""CLI: setup / profile / note."""

from __future__ import annotations

import typer

from guru.cli.catch import CATCH
from guru.cli.console import console
from guru.cli.errors import fail, print_ok
from guru.cli.render import print_profile
from guru.rider.profile_store import (
    load_profile,
    parse_float_list,
    parse_str_list,
    profile_payload,
    set_spot_note,
    update_profile,
)
from guru.search.spots import resolve_spot

__all__ = ("register",)


def register(app: typer.Typer) -> None:
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
            None, "--level", help="beginner | intermediate | advanced | expert"
        ),
        kites: str | None = typer.Option(
            None, "--kites", help="Comma-separated kite sizes m2, e.g. 7,9,12"
        ),
        boards: str | None = typer.Option(
            None, "--boards", help='Comma-separated boards, e.g. "foil 1300, TT 138"'
        ),
        wetsuits: str | None = typer.Option(
            None,
            "--wetsuits",
            help="Comma suits: none,3/2,6/4,6/4+jacket,6/4+jacket+gloves+boots",
        ),
        home_spots: str | None = typer.Option(
            None, "--home-spots", help="Comma-separated favorite spot ids"
        ),
        home_lat: float | None = typer.Option(None, "--home-lat", help="Home latitude"),
        home_lon: float | None = typer.Option(None, "--home-lon", help="Home longitude"),
        drive_km: float | None = typer.Option(
            None, "--drive-km", help="Max drive distance km"
        ),
        range_label: str | None = typer.Option(
            None, "--range-label", help='e.g. "Trabucador -> Leucate"'
        ),
        session_hours: float | None = typer.Option(
            None, "--session-hours", help="Typical session length 2-4 h"
        ),
        as_json: bool = typer.Option(False, "--json"),
    ) -> None:
        """One-shot rider onboarding (flags or --intake paste)."""
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
                    parse_str_list(boards)
                    if boards is not None
                    else parsed.get("boards")
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
                    range_label
                    if range_label is not None
                    else parsed.get("range_label")
                ),
                session_hours=(
                    session_hours
                    if session_hours is not None
                    else parsed.get("session_hours")
                ),
            )
            payload = profile_payload(profile)
        except CATCH as exc:
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
    def profile_cmd(as_json: bool = typer.Option(False, "--json")) -> None:
        """Show rider profile + missing fields for setup."""
        try:
            payload = profile_payload()
            profile = load_profile()
        except CATCH as exc:
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

    @app.command("note")
    def note_cmd(
        spot: str = typer.Argument(..., help="Spot id (or unique name)"),
        text: str = typer.Argument(
            ...,
            help='Local knowledge, e.g. "dirs=SW-W offshore=N-NE Bunker dies in NE"',
        ),
        as_json: bool = typer.Option(False, "--json"),
    ) -> None:
        """Save spot-specific local knowledge."""
        try:
            profile = load_profile()
            resolved = resolve_spot(
                spot,
                prefer_lat=profile.home_lat,
                prefer_lon=profile.home_lon,
            )
            updated = set_spot_note(resolved.id, text)
            payload = {
                "spot_id": resolved.id,
                "name": resolved.name,
                "note": updated.spot_notes.get(str(resolved.id)),
                "spot_notes": updated.spot_notes,
            }
        except CATCH as exc:
            fail(exc, as_json=as_json)
        if as_json:
            print_ok(payload)
            return
        console.print(
            f"[bold]Local note[/bold] {resolved.name} ({resolved.id}): "
            f"{payload['note']}"
        )
