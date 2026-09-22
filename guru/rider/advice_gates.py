"""Long-drive and spot-note helpers for advice (thin)."""

from __future__ import annotations

from guru.models.advice import AdviceWindow
from guru.models.forecast import Forecast
from guru.models.profile import RiderProfile
from guru.rider import voice
from guru.rider.sizing import LONG_DRIVE_KM, MIN_GO_HOURS_LONG_DRIVE, window_duration_hours

__all__ = ("apply_long_drive_gate", "apply_spot_note")


def apply_spot_note(note: str, profile: RiderProfile, forecast: Forecast) -> str:
    local = profile.spot_notes.get(str(forecast.spot.id))
    if not local:
        return note
    from guru.rider.shore import parse_note_sectors

    _, _, remainder = parse_note_sectors(local)
    text = remainder or local
    if not text:
        return note
    tag = f"local: {text}"
    return f"{note}; {tag}" if note else tag


def apply_long_drive_gate(
    overall: str,
    windows: list[AdviceWindow],
    *,
    drive_km: float | None,
) -> str:
    if drive_km is None or drive_km <= LONG_DRIVE_KM:
        return overall
    go_hours = max(
        (
            window_duration_hours(w.start, w.end)
            for w in windows
            if w.verdict == "go"
        ),
        default=0.0,
    )
    if overall == "marginal":
        for w in windows:
            if w.verdict == "marginal":
                w.note = voice.far_drive_note(w.note)
        return "no"
    if overall == "go" and go_hours < MIN_GO_HOURS_LONG_DRIVE:
        for w in windows:
            if w.verdict == "go":
                extra = f"long haul wants ≥{MIN_GO_HOURS_LONG_DRIVE:g}h continuous GO"
                w.note = voice.far_drive_note(
                    f"{w.note}; {extra}" if w.note else extra
                )
        return "no"
    return overall
