"""Pure kite sizing + hour verdicts (no I/O).

Wetsuit ladder lives in ``guru.rider.suit``.
"""

from __future__ import annotations

from guru.models.profile import Level, Sport
from guru.rider.suit import pick_owned_wetsuit, recommend_wetsuit

__all__ = (
    "GUSTY_DELTA_KN",
    "KITE_FACTOR",
    "LONG_DRIVE_KM",
    "MIN_GO_HOURS_LONG_DRIVE",
    "NEAR_DRIVE_KM",
    "SMOOTH_GUST_DELTA_KN",
    "hour_verdict",
    "ideal_kite_m2",
    "kiter_checklist",
    "min_wind_kn",
    "pick_owned_kite",
    "pick_owned_wetsuit",
    "recommend_wetsuit",
    "sizing_rule_text",
    "wind_quality",
    "window_duration_hours",
)

KITE_FACTOR = 2.2
FOIL_SIZE_FACTOR = 0.60
SURFKITE_SIZE_FACTOR = 0.85

LONG_DRIVE_KM = 150.0
NEAR_DRIVE_KM = 60.0  # ~1 h -- soft boost in weekend ranking
MIN_GO_HOURS_LONG_DRIVE = 2.0

_MIN_WIND: dict[Sport, dict[Level, float]] = {
    Sport.KITESURF: {
        Level.BEGINNER: 14.0,
        Level.INTERMEDIATE: 13.0,
        Level.ADVANCED: 11.0,
        Level.EXPERT: 10.0,
    },
    Sport.KITEFOIL: {
        Level.BEGINNER: 12.0,
        Level.INTERMEDIATE: 9.0,
        Level.ADVANCED: 8.0,
        Level.EXPERT: 7.0,
    },
    Sport.SURFKITE: {
        Level.BEGINNER: 13.0,
        Level.INTERMEDIATE: 11.0,
        Level.ADVANCED: 10.0,
        Level.EXPERT: 9.0,
    },
}

SMOOTH_GUST_DELTA_KN = 5.0
GUSTY_DELTA_KN = 8.0


def min_wind_kn(sport: Sport, level: Level = Level.INTERMEDIATE) -> float:
    return _MIN_WIND[sport][level]


def ideal_kite_m2(
    weight_kg: float,
    wind_kn: float,
    *,
    sport: Sport = Sport.KITESURF,
    level: Level = Level.INTERMEDIATE,
    gust_kn: float | None = None,  # kept for callers; sizing uses average
) -> float | None:
    """Ideal canopy m² sized on average wind (gusts -> warning, not downsize)."""
    _ = gust_kn
    if wind_kn is None or wind_kn <= 0 or weight_kg <= 0:
        return None
    base = KITE_FACTOR * weight_kg / float(wind_kn)
    if sport is Sport.KITEFOIL:
        base *= FOIL_SIZE_FACTOR
    elif sport is Sport.SURFKITE:
        base *= SURFKITE_SIZE_FACTOR
    if level is Level.BEGINNER:
        base *= 0.92
    elif level is Level.EXPERT:
        base *= 1.04
    return round(base * 2.0) / 2.0


def pick_owned_kite(
    ideal_m2: float | None,
    owned: list[float],
    *,
    level: Level = Level.INTERMEDIATE,
    sport: Sport = Sport.KITESURF,
) -> tuple[float | None, float | None]:
    """Nearest owned size; level/sport break ties (beginner smaller, advanced larger)."""
    if ideal_m2 is None or not owned:
        return None, None

    def sort_key(size: float) -> tuple[float, int]:
        gap = abs(size - ideal_m2)
        if level is Level.BEGINNER or sport is Sport.KITEFOIL:
            tie = 0 if size <= ideal_m2 else 1
        elif level in {Level.ADVANCED, Level.EXPERT}:
            tie = 0 if size >= ideal_m2 else 1
        else:
            tie = 0
        return (gap, tie)

    best = min(owned, key=sort_key)
    return best, round(best - ideal_m2, 2)


def wind_quality(wind_kn: float | None, gust_kn: float | None) -> str:
    if wind_kn is None:
        return "unknown"
    gust = gust_kn if gust_kn is not None else wind_kn
    spread = gust - wind_kn
    if spread <= SMOOTH_GUST_DELTA_KN:
        return "smooth"
    if spread >= GUSTY_DELTA_KN:
        return "gusty"
    return "ok"


def hour_verdict(
    wind_kn: float | None,
    gust_kn: float | None,
    *,
    sport: Sport,
    level: Level,
) -> str:
    """go | marginal | no for a single hour."""
    if wind_kn is None or wind_kn <= 0:
        return "no"
    floor = min_wind_kn(sport, level)
    gust = gust_kn if gust_kn is not None else wind_kn
    if wind_kn < floor - 2:
        return "no"
    if wind_kn < floor:
        return "marginal"
    # Gusty: warn in notes; beginners stay MARGINAL, others can still GO
    if gust - wind_kn >= GUSTY_DELTA_KN and level is Level.BEGINNER:
        return "marginal"
    if sport is Sport.KITEFOIL and wind_kn >= 28:
        return "marginal"
    if sport is not Sport.KITEFOIL and wind_kn >= 35:
        return "marginal"
    return "go"


def sizing_rule_text(sport: Sport) -> str:
    parts = ["2.2*kg/kn", "size for average", "gusty -> warn"]
    if sport is Sport.KITEFOIL:
        parts.append("foil -40%")
    elif sport is Sport.SURFKITE:
        parts.append("surfkite -15%")
    return "; ".join(parts)


def window_duration_hours(start_iso: str, end_iso: str) -> float:
    from datetime import datetime

    def parse(raw: str) -> datetime:
        text = raw.replace("Z", "+00:00")
        return datetime.fromisoformat(text)

    try:
        return max(0.0, (parse(end_iso) - parse(start_iso)).total_seconds() / 3600.0)
    except ValueError:
        return 0.0


def kiter_checklist(*, gusty: bool, drive_km: float | None = None) -> list[str]:
    from guru.rider import voice

    return voice.checklist(gusty=gusty, drive_km=drive_km)
