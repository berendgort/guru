"""Spot search + meta — Windguru ``search_spots`` / ``forecast_spot``."""

from __future__ import annotations

from guru.models.forecast import Spot
from guru.search.client import IAPI_CZ, get_client
from guru.search.exceptions import GuruNotFoundError


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
    data = get_client().get_json(
        params={"q": "forecast_spot", "id_spot": spot_id},
        referer=f"https://www.windguru.cz/{spot_id}",
        base=IAPI_CZ,
    )
    spots = data.get("spots") or {}
    meta = spots.get(str(spot_id)) or spots.get(spot_id)
    if not meta and data.get("tabs"):
        tab = data["tabs"][0]
        return Spot(
            id=int(tab.get("id_spot") or spot_id),
            name=f"spot-{spot_id}",
            lat=_f(tab.get("lat")),
            lon=_f(tab.get("lon")),
        )
    if not meta:
        raise GuruNotFoundError(f"Spot {spot_id} not found")
    return Spot(
        id=int(meta.get("id_spot") or spot_id),
        name=str(meta.get("spotname") or f"spot-{spot_id}"),
        country=meta.get("country"),
        lat=_f(meta.get("lat")),
        lon=_f(meta.get("lon")),
        alt=_f(meta.get("alt")),
    )


def _f(v: object) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(v)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
