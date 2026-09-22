"""Nearby spots via free ``q=spots&opt=simplemap`` (map markers)."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from guru.models.forecast import Spot
from guru.search.client import IAPI_CZ, get_client

_simplemap_cache: list[tuple[int, str, float, float]] | None = None


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def load_simplemap_spots(*, force: bool = False) -> list[tuple[int, str, float, float]]:
    """Return ``(id, name, lat, lon)`` for all free map spots."""
    global _simplemap_cache
    if _simplemap_cache is not None and not force:
        return _simplemap_cache
    data = get_client().get_json(
        params={"q": "spots", "opt": "simplemap", "WGCACHEABLE": 1800},
        referer="https://www.windguru.cz/map/spot/",
        base=IAPI_CZ,
    )
    rows = _parse_simplemap_rows(data.get("spots") or [])
    _simplemap_cache = rows
    return rows


def _parse_simplemap_rows(raw: Sequence[Any]) -> list[tuple[int, str, float, float]]:
    rows: list[tuple[int, str, float, float]] = []
    for row in raw:
        if not isinstance(row, (list, tuple)) or len(row) < 4:
            continue
        try:
            rows.append((int(row[0]), str(row[1] or ""), float(row[2]), float(row[3])))
        except (TypeError, ValueError):
            continue
    return rows


def rank_near(
    rows: Sequence[tuple[int, str, float, float]],
    lat: float,
    lon: float,
    *,
    radius_km: float = 50.0,
    limit: int = 20,
) -> list[Spot]:
    scored: list[tuple[float, Spot]] = []
    for sid, name, slat, slon in rows:
        d = haversine_km(lat, lon, slat, slon)
        if d <= radius_km:
            scored.append(
                (d, Spot(id=sid, name=name or f"spot-{sid}", lat=slat, lon=slon))
            )
    scored.sort(key=lambda x: x[0])
    return [s for _, s in scored[:limit]]


def spots_near(
    lat: float,
    lon: float,
    *,
    radius_km: float = 50.0,
    limit: int = 20,
) -> list[Spot]:
    """Named Windguru spots within ``radius_km`` of a point (free, no PRO)."""
    return rank_near(
        load_simplemap_spots(), lat, lon, radius_km=radius_km, limit=limit
    )


def spots_near_from_rows(
    rows: list[Any],
    lat: float,
    lon: float,
    *,
    radius_km: float = 50.0,
    limit: int = 20,
) -> list[Spot]:
    """Offline helper for tests — same ranking over a fixture subset."""
    return rank_near(
        _parse_simplemap_rows(rows), lat, lon, radius_km=radius_km, limit=limit
    )
