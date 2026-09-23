"""Next kite-weekend window + model coverage (pure)."""

from __future__ import annotations

__all__ = (
    "FRI_EVENING_HOUR_UTC",
    "coverage_note",
    "filter_day_candidates_to_window",
    "filter_slots_to_window",
    "forecast_reaches",
    "hours_to_cover",
    "in_kite_weekend",
    "is_kite_weekend_instant",
    "model_weekend_coverage",
    "next_kite_weekend",
    "parse_iso_utc",
    "slot_in_kite_weekend",
    "slot_is_kite_weekend_day",
)

from datetime import datetime, timedelta, timezone
from typing import Any

from guru.models.advice import DEFAULT_WEEKEND_HOURS, ScheduleSlot
from guru.models.blend import BlendWeight
from guru.models.forecast import Forecast

# Surrogate for "Friday evening" without spot TZ (after-work session).
FRI_EVENING_HOUR_UTC = 15


def parse_iso_utc(raw: str) -> datetime | None:
    """Parse ISO timestamp to aware UTC; None on garbage."""
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def is_kite_weekend_instant(dt: datetime) -> bool:
    """Fri evening / Sat / Sun (no date window). Single Fri-eve rule."""
    dt = dt.astimezone(timezone.utc)
    wd = dt.weekday()
    return wd in {5, 6} or (wd == 4 and dt.hour >= FRI_EVENING_HOUR_UTC)


def _fri_evening(day: datetime) -> datetime:
    return day.astimezone(timezone.utc).replace(
        hour=FRI_EVENING_HOUR_UTC, minute=0, second=0, microsecond=0
    )


def next_kite_weekend(
    now: datetime | None = None,
) -> tuple[datetime, datetime]:
    """Upcoming Fri eve UTC -> Sun 23:59 UTC (this weekend if already in it)."""
    now = (now or datetime.now(tz=timezone.utc)).astimezone(timezone.utc)
    if is_kite_weekend_instant(now):
        # Same Fri eve for Fri evening / Sat / Sun.
        fri = _fri_evening(now - timedelta(days=(now.weekday() - 4) % 7))
    else:
        fri = _fri_evening(now + timedelta(days=(4 - now.weekday()) % 7))
        if fri <= now:
            fri += timedelta(days=7)
    sun = (fri + timedelta(days=2)).replace(
        hour=23, minute=59, second=0, microsecond=0
    )
    return fri, sun


def hours_to_cover(now: datetime, end: datetime, *, pad: int = 12) -> int:
    """Forecast steps needed to reach ``end`` (hourly models) + pad."""
    now = now.astimezone(timezone.utc)
    end = end.astimezone(timezone.utc)
    hours = int((end - now).total_seconds() // 3600) + pad
    return max(48, min(hours, DEFAULT_WEEKEND_HOURS))


def in_kite_weekend(dt: datetime, start: datetime, end: datetime) -> bool:
    """True if ``dt`` is Fri evening / Sat / Sun inside [start, end]."""
    dt = dt.astimezone(timezone.utc)
    start = start.astimezone(timezone.utc)
    end = end.astimezone(timezone.utc)
    if dt < start or dt > end:
        return False
    return is_kite_weekend_instant(dt)


def slot_is_kite_weekend_day(slot: ScheduleSlot) -> bool:
    """Bound-free Fri-eve/Sat/Sun check (for ``where --day weekend``)."""
    dt = parse_iso_utc(slot.start)
    return dt is not None and is_kite_weekend_instant(dt)


def slot_in_kite_weekend(
    slot: ScheduleSlot, start: datetime, end: datetime
) -> bool:
    dt = parse_iso_utc(slot.start)
    return dt is not None and in_kite_weekend(dt, start, end)


def filter_slots_to_window(
    schedule: list[ScheduleSlot], start: datetime, end: datetime
) -> list[ScheduleSlot]:
    return [s for s in schedule if slot_in_kite_weekend(s, start, end)]


def filter_day_candidates_to_window(
    candidates: list[tuple[str, ScheduleSlot, float]],
    start: datetime,
    end: datetime,
) -> list[tuple[str, ScheduleSlot, float]]:
    """Drop out-of-window day candidates before pick_schedule."""
    return [
        (d, slot, rank)
        for d, slot, rank in candidates
        if slot_in_kite_weekend(slot, start, end)
    ]


def forecast_reaches(fc: Forecast, until: datetime) -> bool:
    if not fc.hours:
        return False
    last = fc.hours[-1].time
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    return last >= until.astimezone(timezone.utc)


def model_weekend_coverage(
    models: list[BlendWeight],
    forecasts: list[Forecast],
    *,
    weekend_start: datetime,
    weekend_end: datetime,
) -> dict[str, Any]:
    """Which WINDGURU_DEFAULT models reach Fri evening / end of Sunday."""
    sat_noon = (weekend_start + timedelta(days=1)).replace(
        hour=12, minute=0, second=0, microsecond=0
    )
    rows: list[dict[str, Any]] = []
    weight_to_fri = 0.0
    weight_to_sat = 0.0
    weight_to_sun = 0.0
    for bw, fc in zip(models, forecasts, strict=True):
        to_fri = forecast_reaches(fc, weekend_start)
        to_sat = forecast_reaches(fc, sat_noon)
        to_sun = forecast_reaches(fc, weekend_end)
        rows.append(
            {
                "id_model": bw.id_model,
                "name": bw.name,
                "weight_pct": bw.weight_pct,
                "rank": bw.rank,
                "reaches_fri_evening": to_fri,
                "reaches_saturday": to_sat,
                "reaches_sunday": to_sun,
            }
        )
        if to_fri:
            weight_to_fri += bw.weight_pct
        if to_sat:
            weight_to_sat += bw.weight_pct
        if to_sun:
            weight_to_sun += bw.weight_pct

    # High-% Tune models often stop at ~2-3d; weekend beyond that is thin.
    primary_ok = bool(rows) and rows[0].get("reaches_saturday") is True
    uncertain = (not primary_ok) or weight_to_sat < 50.0
    return {
        "models": rows,
        "weight_pct_to_fri_evening": round(weight_to_fri, 1),
        "weight_pct_to_saturday": round(weight_to_sat, 1),
        "weight_pct_to_sunday": round(weight_to_sun, 1),
        "uncertain": uncertain,
        "note": coverage_note(rows, uncertain=uncertain, weight_sat=weight_to_sat),
    }


def coverage_note(
    rows: list[dict[str, Any]],
    *,
    uncertain: bool,
    weight_sat: float,
) -> str:
    if not rows:
        return "No WINDGURU_DEFAULT models returned -- cannot call the weekend."
    short = [
        str(r["name"])
        for r in rows
        if not r.get("reaches_saturday")
    ]
    if not uncertain:
        return (
            f"WINDGURU_DEFAULT coverage OK through Saturday "
            f"({weight_sat:g}% weight reaches Sat)."
        )
    if short:
        return (
            f"UNCERTAIN weekend call: high-% models not in range yet "
            f"({', '.join(short)} stop short of Saturday; "
            f"only {weight_sat:g}% weight reaches Sat). "
            "Treat as early look -- re-check closer to Fri."
        )
    return (
        f"UNCERTAIN weekend call: only {weight_sat:g}% WINDGURU_DEFAULT "
        "weight reaches Saturday. Re-check closer to Fri."
    )
