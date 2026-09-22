"""Spot search + meta -- Windguru ``search_spots`` / ``forecast_spot``."""

from __future__ import annotations

__all__ = (
    "fetch_forecast_spot",
    "get_spot",
    "resolve_spot",
    "search_spots",
    "spot_from_forecast_spot",
)

from typing import Any

from guru.models.forecast import Spot
from guru.search.client import IAPI_CZ, get_client
from guru.search.exceptions import GuruAmbiguousError, GuruNotFoundError, GuruParseError


def _as_float(v: object) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(v)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def fetch_forecast_spot(spot_id: int) -> dict[str, Any]:
    return get_client().get_json(
        params={"q": "forecast_spot", "id_spot": spot_id},
        referer=f"https://www.windguru.cz/{spot_id}",
        base=IAPI_CZ,
    )


def spot_from_forecast_spot(data: dict[str, Any], spot_id: int) -> Spot:
    """Decode Spot from a ``forecast_spot`` payload."""
    spots = data.get("spots") or {}
    meta = spots.get(str(spot_id)) or spots.get(spot_id)
    if not meta and data.get("tabs"):
        tab = data["tabs"][0]
        return Spot(
            id=int(tab.get("id_spot") or spot_id),
            name=f"spot-{spot_id}",
            lat=_as_float(tab.get("lat")),
            lon=_as_float(tab.get("lon")),
        )
    if not meta:
        raise GuruNotFoundError(f"Spot {spot_id} not found")
    if not isinstance(meta, dict):
        raise GuruParseError(f"Invalid spot meta for {spot_id}")
    return Spot(
        id=int(meta.get("id_spot") or spot_id),
        name=str(meta.get("spotname") or f"spot-{spot_id}"),
        country=meta.get("country"),
        lat=_as_float(meta.get("lat")),
        lon=_as_float(meta.get("lon")),
        alt=_as_float(meta.get("alt")),
    )


def search_spots(query: str, *, limit: int = 20) -> list[Spot]:
    data = get_client().get_json(
        params={"q": "search_spots", "search": query},
        referer="https://www.windguru.cz/",
        base=IAPI_CZ,
    )
    out: list[Spot] = []
    for row in (data.get("spots") or [])[:limit]:
        out.append(
            Spot(
                id=int(row["id_spot"]),
                name=str(row.get("spotname") or ""),
                country=row.get("country"),
                nickname=row.get("nickname"),
            )
        )
    return out


def get_spot(spot_id: int) -> Spot:
    return spot_from_forecast_spot(fetch_forecast_spot(spot_id), spot_id)


def resolve_spot(
    spot: str,
    *,
    pick: int | None = None,
    prefer_lat: float | None = None,
    prefer_lon: float | None = None,
) -> Spot:
    """Resolve a numeric id or unique name. Multiple hits → closest or ambiguous."""
    text = spot.strip()
    if text.isdigit():
        return get_spot(int(text))

    hits = search_spots(text, limit=10)
    if pick is not None:
        if hits and pick not in {h.id for h in hits}:
            raise GuruNotFoundError(
                f"Spot id {pick} is not among matches for {spot!r}"
            )
        return get_spot(pick)

    if not hits:
        raise GuruNotFoundError(f"No spots matching {spot!r}")
    if len(hits) == 1:
        return get_spot(hits[0].id)
    exact = [h for h in hits if h.name.lower() == text.lower()]
    if len(exact) == 1:
        return get_spot(exact[0].id)

    # Ambiguous: prefer closest to home when coords known (questionnaire 5A)
    if prefer_lat is not None and prefer_lon is not None:
        from guru.search.near import haversine_km

        with_coords = [h for h in hits if h.lat is not None and h.lon is not None]
        if with_coords:
            closest = min(
                with_coords,
                key=lambda h: haversine_km(
                    prefer_lat, prefer_lon, float(h.lat), float(h.lon)
                ),
            )
            return get_spot(closest.id)

    raise GuruAmbiguousError(
        f"Ambiguous spot {spot!r}: {len(hits)} matches -- pass a numeric id or --pick <id>",
        candidates=hits,
    )
