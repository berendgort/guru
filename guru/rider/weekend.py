"""Weekend / drive-range spot scanner — 'where can I kite?'."""

from __future__ import annotations

from guru.models.forecast import Spot
from guru.models.profile import (
    RiderProfile,
    WeekendReport,
    WeekendSpotAdvice,
)
from guru.rider.advice import advise_forecast
from guru.rider.sizing import kiter_checklist
from guru.search.blend import get_best_forecast
from guru.search.near import haversine_km, spots_near
from guru.search.spots import get_spot

_VERDICT_RANK = {"go": 2, "marginal": 1, "no": 0, "incomplete": -1}


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
            d = haversine_km(
                profile.home_lat, profile.home_lon, spot.lat, spot.lon
            )
        by_id[sid] = (spot, d)

    rows = list(by_id.values())
    rows.sort(key=lambda x: (x[1] is None, x[1] if x[1] is not None else 9999))
    return rows[:limit]


def scan_weekend(
    profile: RiderProfile,
    *,
    hours: int = 48,
    limit_spots: int = 8,
    top_models: int = 1,
) -> WeekendReport:
    """Rank rideable spots in the rider's drive corridor."""
    missing = profile.missing_fields() + profile.missing_range_fields()
    thinking = kiter_checklist(gusty=False, drive_km=profile.drive_km)
    thinking.insert(
        0,
        "Scan named spots in drive range; farther trips need clearer GO",
    )
    if profile.range_label:
        thinking.insert(0, f"Home range: {profile.range_label}")

    if missing:
        return WeekendReport(
            verdict="incomplete",
            range_label=profile.range_label,
            home_lat=profile.home_lat,
            home_lon=profile.home_lon,
            drive_km=profile.drive_km,
            missing_profile=missing,
            summary=f"Need profile + home range — missing: {', '.join(missing)}",
            thinking=thinking,
        )

    candidates = candidate_spots(profile, limit=limit_spots)
    results: list[WeekendSpotAdvice] = []
    for spot, drive in candidates:
        best = get_best_forecast(spot.id, top=top_models, hours=hours)
        if not best.forecasts:
            continue
        advice = advise_forecast(
            best.forecasts[0], profile, drive_km=drive
        )
        if advice.verdict in {"no", "incomplete"}:
            continue
        # Far drive: only keep clear GO
        if drive is not None and drive > 90 and advice.verdict != "go":
            continue
        window = advice.windows[0] if advice.windows else None
        score = _score(advice.verdict, drive)
        results.append(
            WeekendSpotAdvice(
                spot_id=spot.id,
                name=spot.name,
                lat=spot.lat,
                lon=spot.lon,
                drive_km=round(drive, 1) if drive is not None else None,
                verdict=advice.verdict,
                summary=advice.summary,
                best_window=window,
                model=advice.model,
                score=score,
            )
        )

    results.sort(key=lambda r: (-r.score, r.drive_km if r.drive_km is not None else 999))
    overall = results[0].verdict if results else "no"
    if results:
        top = results[0]
        summary = (
            f"{overall.upper()}: {top.name} ({top.spot_id}) "
            f"~{top.drive_km or '?'} km — {top.summary}"
        )
    else:
        summary = "No rideable spot in your drive range for this forecast window."

    return WeekendReport(
        verdict=overall,
        range_label=profile.range_label,
        home_lat=profile.home_lat,
        home_lon=profile.home_lon,
        drive_km=profile.drive_km,
        spots=results,
        missing_profile=[],
        summary=summary,
        thinking=thinking,
    )


def _score(verdict: str, drive_km: float | None) -> float:
    base = float(_VERDICT_RANK.get(verdict, 0)) * 100.0
    if drive_km is None:
        return base
    return base - drive_km
