"""Daylight + precip helpers for advice windows (pure, no I/O)."""

from __future__ import annotations

from datetime import datetime

__all__ = (
    "PRECIP_SOFT_MM",
    "in_daylight",
    "minutes_of_day",
    "parse_hhmm",
)

PRECIP_SOFT_MM = 1.5


def parse_hhmm(raw: str | None) -> int | None:
    """Return minutes from midnight for ``HH:MM`` (or None)."""
    if not raw or ":" not in raw:
        return None
    try:
        hh, mm = raw.strip().split(":", 1)
        return int(hh) * 60 + int(mm)
    except ValueError:
        return None


def minutes_of_day(dt: datetime) -> int:
    return dt.hour * 60 + dt.minute


def in_daylight(
    dt: datetime,
    sunrise: str | None,
    sunset: str | None,
) -> bool:
    """True if inside sunrise-sunset, or if either bound is missing."""
    start = parse_hhmm(sunrise)
    end = parse_hhmm(sunset)
    if start is None or end is None:
        return True
    now = minutes_of_day(dt)
    if start <= end:
        return start <= now <= end
    return now >= start or now <= end
