"""Weekend candidate spots + long-drive gate (I/O + pure helpers)."""

from __future__ import annotations

from datetime import datetime

from guru.models.advice import AdviceWindow
from guru.models.forecast import Spot
from guru.models.profile import RiderProfile
from guru.rider.sizing import LONG_DRIVE_KM, MIN_GO_HOURS_LONG_DRIVE, window_duration_hours
from guru.search.near import haversine_km, spots_near
from guru.search.spots import get_spot

__all__ = ("candidate_spots", "long_drive_ok", "weekday_label")


def candidate_spots(
    profile: RiderProfile,
    *,
    limit: int = 12,
) -> list[tuple[Spot, float | None]]:
    """Spots in drive range + explicit home_spots. Returns (spot, drive_km)."""
    by_id: dict[int, tuple[Spot, float | None]] = {}

    if profile.home_lat is not None and profile.home_lon is not None:
        radius = float(profile.drive_km or 80.0)
        near = spots_near(
            profile.home_lat, profile.home_lon, radius_km=radius, limit=limit
        )
        for s in near:
            d = None
            if s.lat is not None and s.lon is not None:
                d = haversine_km(profile.home_lat, profile.home_lon, s.lat, s.lon)
            by_id[s.id] = (s, d)

    for sid in profile.home_spots:
        if sid in by_id:
            continue
        spot = get_spot(sid)
        d = None
        if (
            profile.home_lat is not None
            and profile.home_lon is not None
            and spot.lat is not None
            and spot.lon is not None
        ):
            d = haversine_km(profile.home_lat, profile.home_lon, spot.lat, spot.lon)
        by_id[sid] = (spot, d)

    rows = list(by_id.values())
    rows.sort(key=lambda x: (x[1] is None, x[1] if x[1] is not None else 9999))
    return rows[:limit]


def long_drive_ok(
    drive: float | None,
    *,
    verdict: str | None = None,
    windows: list[AdviceWindow] | None = None,
    window: AdviceWindow | None = None,
) -> bool:
    """Long haul (>150 km) needs clear GO with >=2h continuous window."""
    if drive is None or drive <= LONG_DRIVE_KM:
        return True
    if window is not None:
        if window.verdict != "go":
            return False
        return window_duration_hours(window.start, window.end) >= MIN_GO_HOURS_LONG_DRIVE
    if verdict is not None and windows is not None:
        if verdict != "go":
            return False
        go_h = max(
            (
                window_duration_hours(w.start, w.end)
                for w in windows
                if w.verdict == "go"
            ),
            default=0.0,
        )
        return go_h >= MIN_GO_HOURS_LONG_DRIVE
    return True


def weekday_label(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return iso[:10]
    return dt.strftime("%a")
