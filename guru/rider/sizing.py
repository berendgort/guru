"""Pure kite / wetsuit sizing math (no I/O) — kiteboarding-oriented."""

from __future__ import annotations

from guru.models.profile import Level, Sport

# Twin-tip rule of thumb (WindUp / Surf Store): m² ≈ 2.2 × kg ÷ knots
KITE_FACTOR = 2.2
FOIL_SIZE_FACTOR = 0.60  # ~40% smaller than twin-tip
SURFKITE_SIZE_FACTOR = 0.85  # ~15% smaller / −1–2 m²

# Minimum average wind (kt) by sport × level
_MIN_WIND: dict[Sport, dict[Level, float]] = {
    Sport.KITESURF: {
        Level.BEGINNER: 14.0,
        Level.INTERMEDIATE: 12.0,
        Level.ADVANCED: 11.0,
    },
    Sport.KITEFOIL: {
        Level.BEGINNER: 12.0,
        Level.INTERMEDIATE: 9.0,
        Level.ADVANCED: 8.0,
    },
    Sport.SURFKITE: {
        Level.BEGINNER: 13.0,
        Level.INTERMEDIATE: 11.0,
        Level.ADVANCED: 10.0,
    },
}

# Gust spread (gust − wind): kiters treat ≤5 as smooth, ≥8 as hard work
SMOOTH_GUST_DELTA_KN = 5.0
GUSTY_DELTA_KN = 8.0

# Warmth rank: 0 = coldest kit … 5 = boardshorts
# Kiteboarding: mostly above water → air temp + wind chill dominate (Session Sports / O'Neill)
_RANK_LABELS: list[str] = [
    "5/4+hood",
    "5/4",
    "4/3",
    "3/2",
    "shorty",
    "lycra",
]

# Base rank from air °C (proxy until water temp exists)
_TEMP_RANK: list[tuple[float, int]] = [
    (-50.0, 0),  # <8 → 5/4+hood
    (8.0, 1),  # 8–12 → 5/4
    (12.0, 2),  # 12–15 → 4/3
    (15.0, 3),  # 15–19 → 3/2
    (19.0, 4),  # 19–23 → shorty
    (23.0, 5),  # 23+ → lycra
]

_WETSUIT_RANK: dict[str, int] = {
    "5/4+hood": 0,
    "5/4": 1,
    "5/3": 1,
    "4/3": 2,
    "3/2": 3,
    "2mm": 4,
    "shorty": 4,
    "springsuit": 4,
    "lycra": 5,
    "rashguard": 5,
    "boardshorts": 5,
}


def min_wind_kn(sport: Sport, level: Level = Level.INTERMEDIATE) -> float:
    return _MIN_WIND[sport][level]


def ideal_kite_m2(
    weight_kg: float,
    wind_kn: float,
    *,
    sport: Sport = Sport.KITESURF,
    level: Level = Level.INTERMEDIATE,
    gust_kn: float | None = None,
) -> float | None:
    """Ideal canopy m²; sizes for gusts when provided."""
    design = gust_kn if gust_kn is not None and gust_kn > 0 else wind_kn
    if design is None or design <= 0 or weight_kg <= 0:
        return None
    base = KITE_FACTOR * weight_kg / float(design)
    if sport is Sport.KITEFOIL:
        base *= FOIL_SIZE_FACTOR
    elif sport is Sport.SURFKITE:
        base *= SURFKITE_SIZE_FACTOR
    if level is Level.BEGINNER:
        base *= 0.92
    return round(base * 2.0) / 2.0


def pick_owned_kite(
    ideal_m2: float | None,
    owned: list[float],
) -> tuple[float | None, float | None]:
    """Return (owned_m2, gap_m2) closest to ideal."""
    if ideal_m2 is None or not owned:
        return None, None
    best = min(owned, key=lambda size: abs(size - ideal_m2))
    return best, round(best - ideal_m2, 2)


def _base_rank_from_temp(temp_c: float) -> int:
    rank = 0
    for min_t, r in _TEMP_RANK:
        if temp_c >= min_t:
            rank = r
    return rank


def recommend_wetsuit(
    temp_c: float | None,
    *,
    wind_kn: float | None = None,
    session_hours: float = 3.0,
    level: Level = Level.INTERMEDIATE,
) -> tuple[str | None, list[str]]:
    """Kiteboarding suit for a 2–4 h session.

    Returns ``(label, accessories)``. Kiters stay mostly above water — wind
    chill and session length push warmer than a surf chart at the same °C.
    """
    if temp_c is None:
        return None, []

    rank = _base_rank_from_temp(temp_c)

    # Wind chill (Session Sports / kite guides): size up when windy
    wind = wind_kn or 0.0
    if wind >= 25:
        rank -= 2
    elif wind >= 15:
        rank -= 1

    # Longer sessions cool you down (BreakFinder-style duration bump)
    if session_hours >= 4.0:
        rank -= 2
    elif session_hours >= 3.0:
        rank -= 1
    # 2 h = baseline (no bump)

    # Beginners spend more time in the water / waiting
    if level is Level.BEGINNER:
        rank -= 1
    elif level is Level.ADVANCED and session_hours <= 2.0:
        rank += 1  # short hot lap

    rank = max(0, min(len(_RANK_LABELS) - 1, rank))
    label = _RANK_LABELS[rank]

    accessories: list[str] = []
    if rank <= 1:
        accessories.extend(["boots", "gloves", "hood"])
    elif rank == 2 and (temp_c < 14 or wind >= 18):
        accessories.extend(["boots"])
    return label, accessories


def _normalize_suit(raw: str) -> str:
    key = raw.strip().lower().replace(" ", "").replace("mm", "")
    aliases = {
        "5/4hood": "5/4+hood",
        "5/4+hood": "5/4+hood",
        "hooded": "5/4+hood",
        "5/4": "5/4",
        "5/3": "5/3",
        "4/3": "4/3",
        "3/2": "3/2",
        "2": "2mm",
        "2mm": "2mm",
        "shorty": "shorty",
        "spring": "shorty",
        "springsuit": "shorty",
        "lycra": "lycra",
        "rash": "lycra",
        "rashguard": "lycra",
        "boardshorts": "lycra",
        "shorts": "lycra",
    }
    return aliases.get(key, key)


def pick_owned_wetsuit(
    recommended: str | None,
    owned: list[str],
) -> str | None:
    if recommended is None or not owned:
        return None
    want = _WETSUIT_RANK.get(_normalize_suit(recommended))
    if want is None:
        return owned[0]
    best: str | None = None
    best_dist = 99
    for suit in owned:
        rank = _WETSUIT_RANK.get(_normalize_suit(suit))
        if rank is None:
            continue
        dist = abs(rank - want)
        if dist < best_dist:
            best_dist = dist
            best = suit
    return best or owned[0]


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
    if gust - wind_kn >= GUSTY_DELTA_KN:
        return "marginal"
    if sport is Sport.KITEFOIL and wind_kn >= 28:
        return "marginal"
    if sport is not Sport.KITEFOIL and wind_kn >= 35:
        return "marginal"
    return "go"


def sizing_rule_text(sport: Sport) -> str:
    parts = ["2.2*kg/kn", "size for gusts"]
    if sport is Sport.KITEFOIL:
        parts.append("foil -40%")
    elif sport is Sport.SURFKITE:
        parts.append("surfkite -15%")
    return "; ".join(parts)


def kiter_checklist(*, gusty: bool, drive_km: float | None = None) -> list[str]:
    """How kiters think before leaving (CLEAR / kitesurfbase habits)."""
    items = [
        "Confirm average + gusts (size for gusts, not lulls)",
        "At beach: watch 5 min — direction, consistency, downwind hazards",
        "Prefer side-shore / side-onshore; treat offshore as advanced-only",
        "Cross-check top models agree before a long drive",
    ]
    if gusty:
        items.append("Gusty → smaller kite / more depower / shorter session")
    if drive_km is not None and drive_km > 90:
        items.append(
            f"Long drive (~{drive_km:.0f} km) → require a clear GO, not marginal"
        )
    return items
