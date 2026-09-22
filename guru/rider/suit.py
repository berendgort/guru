"""Wetsuit / accessories ladder for kite sessions (pure).

SST owns thickness when available (Mystic/evo/Billabong water charts).
Air + wind chill (or WCHILL) may only bump warmer (jacket/gloves).
Without SST: air + wind-chill proxy (Windguru free tables have no SST).
"""

from __future__ import annotations

from guru.models.profile import Level

__all__ = (
    "SUIT_LABELS",
    "pick_owned_wetsuit",
    "recommend_wetsuit",
)

SUIT_LABELS: list[str] = [
    "6/4+jacket+gloves+boots",
    "6/4+jacket",
    "6/4",
    "3/2",
    "none",
]

_SUIT_RANK: dict[str, int] = {
    "6/4+jacket+gloves+boots": 0,
    "6/4+gloves+boots": 0,
    "6/4+jacket": 1,
    "6/4": 2,
    "5/4": 2,
    "5/3": 2,
    "4/3": 2,
    "3/2": 3,
    "2mm": 3,
    "shorty": 4,
    "springsuit": 4,
    "lycra": 4,
    "rashguard": 4,
    "boardshorts": 4,
    "none": 4,
    "no": 4,
    "nosuit": 4,
}

# Water-temp chart (SST) and air+chill fallback share the same thresholds
_TEMP_RANK: list[tuple[float, int]] = [
    (-50.0, 0),
    (6.0, 1),
    (10.0, 2),
    (16.0, 3),
    (22.0, 4),
]


def _effective_air_c(
    temp_c: float,
    wind_kn: float | None,
    wchill_c: float | None,
) -> float:
    if wchill_c is not None:
        return wchill_c
    wind = wind_kn or 0.0
    chill = 0.0
    if wind >= 25:
        chill = 5.0
    elif wind >= 18:
        chill = 3.0
    elif wind >= 12:
        chill = 1.5
    return temp_c - chill


def _base_rank(temp_c: float) -> int:
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
    sst_c: float | None = None,
    wchill_c: float | None = None,
) -> tuple[str | None, list[str]]:
    """Return ``(label, accessories)``. SST base; air/WCHILL may only warmth-up."""
    if sst_c is None and temp_c is None:
        return None, []

    if sst_c is not None:
        rank = _base_rank(sst_c)
        if temp_c is not None:
            feel = _effective_air_c(temp_c, wind_kn, wchill_c)
            # feel may only make kit warmer (lower rank number)
            feel_rank = _base_rank(feel)
            if feel <= sst_c - 5 or feel < 12:
                rank = min(rank, feel_rank)
            # boots floor: SST < 12 never thinner than 6/4
            if sst_c < 12:
                rank = min(rank, 2)
    else:
        assert temp_c is not None
        rank = _base_rank(_effective_air_c(temp_c, wind_kn, wchill_c))

    if session_hours >= 4.0:
        rank -= 1
    if level is Level.BEGINNER:
        rank -= 1
    if level is Level.EXPERT and session_hours <= 2.0:
        rank += 1

    rank = max(0, min(len(SUIT_LABELS) - 1, rank))
    label = SUIT_LABELS[rank]
    accessories: list[str] = []
    if "gloves" in label:
        accessories.extend(["gloves", "boots"])
    elif "jacket" in label:
        accessories.append("jacket")
    return label, accessories


def _normalize_suit(raw: str) -> str:
    key = raw.strip().lower().replace(" ", "")
    key = key.replace("mm", "").replace("wetsuit", "")
    aliases = {
        "6/4+jacket+gloves+boots": "6/4+jacket+gloves+boots",
        "6/4jacketglovesboots": "6/4+jacket+gloves+boots",
        "6/4+gloves+boots": "6/4+jacket+gloves+boots",
        "6/4+jacket": "6/4+jacket",
        "6/4jacket": "6/4+jacket",
        "6/4": "6/4",
        "5/4": "6/4",
        "5/3": "6/4",
        "4/3": "6/4",
        "3/2": "3/2",
        "2": "3/2",
        "2mm": "3/2",
        "shorty": "none",
        "spring": "none",
        "lycra": "none",
        "rash": "none",
        "rashguard": "none",
        "boardshorts": "none",
        "shorts": "none",
        "none": "none",
        "no": "none",
        "nosuit": "none",
    }
    return aliases.get(key, key)


def pick_owned_wetsuit(
    recommended: str | None,
    owned: list[str],
) -> str | None:
    if recommended is None or not owned:
        return None
    want = _SUIT_RANK.get(_normalize_suit(recommended))
    if want is None:
        return owned[0]
    best: str | None = None
    best_dist = 99
    for suit in owned:
        rank = _SUIT_RANK.get(_normalize_suit(suit))
        if rank is None:
            continue
        dist = abs(rank - want)
        if dist < best_dist:
            best_dist = dist
            best = suit
    return best or owned[0]
