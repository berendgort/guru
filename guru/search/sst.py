"""Open-Meteo Marine SST -- lightweight JSON, disk cache, no browser."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from curl_cffi import requests as curl_requests

from guru.search.client import DEFAULT_IMPERSONATE, REQUEST_TIMEOUT

__all__ = ("SST_SOURCE", "fetch_sst", "fetch_sst_many", "sst_cache_path")

MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"
CACHE_TTL_S = 12 * 3600
CACHE_SCHEMA = 1
SST_SOURCE = "open-meteo-marine"
_TIMEOUT = min(REQUEST_TIMEOUT, 12.0)


def sst_cache_path() -> Path:
    override = os.environ.get("GURU_CACHE_DIR")
    if override:
        return Path(override).expanduser() / "sst.json"
    xdg = os.environ.get("XDG_CACHE_HOME")
    root = Path(xdg).expanduser() / "guru" if xdg else Path.home() / ".cache" / "guru"
    return root / "sst.json"


def _key(lat: float, lon: float) -> str:
    return f"{round(lat, 2)},{round(lon, 2)}"


def _load() -> dict[str, Any]:
    path = sst_cache_path()
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save(cache: dict[str, Any]) -> None:
    path = sst_cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache), encoding="utf-8")


def _cached(lat: float, lon: float) -> tuple[bool, float | None]:
    """Return (hit, sst_c). hit=True means do not refetch."""
    entry = _load().get(_key(lat, lon))
    if not isinstance(entry, dict):
        return False, None
    if time.time() - float(entry.get("ts", 0)) > CACHE_TTL_S:
        return False, None
    val = entry.get("sst_c")
    return True, (float(val) if val is not None else None)


def _store(lat: float, lon: float, sst_c: float | None, cache: dict[str, Any]) -> None:
    cache[_key(lat, lon)] = {"schema_version": CACHE_SCHEMA, "ts": time.time(), "sst_c": sst_c}


def _parse_sst(payload: Any) -> float | None:
    if not isinstance(payload, dict):
        return None
    val = (payload.get("current") or {}).get("sea_surface_temperature")
    return float(val) if val is not None else None


def _get(params: dict[str, Any]) -> Any | None:
    try:
        session = curl_requests.Session(impersonate=DEFAULT_IMPERSONATE)
        resp = session.get(MARINE_URL, params=params, timeout=_TIMEOUT)
        session.close()
        if resp.status_code >= 400:
            return None
        return resp.json()
    except Exception:  # noqa: BLE001 -- soft fail to air suit path
        return None


def fetch_sst(lat: float, lon: float, *, use_cache: bool = True) -> float | None:
    """Point SST °C. None if inland / miss."""
    if use_cache:
        hit, sst = _cached(lat, lon)
        if hit:
            return sst
    data = _get(
        {
            "latitude": lat,
            "longitude": lon,
            "current": "sea_surface_temperature",
            "cell_selection": "sea",
        }
    )
    sst = _parse_sst(data) if data is not None else None
    if use_cache:
        cache = _load()
        _store(lat, lon, sst, cache)
        _save(cache)
    return sst


def fetch_sst_many(
    coords: list[tuple[float, float]],
    *,
    use_cache: bool = True,
) -> dict[tuple[float, float], float | None]:
    """Batch SST (one HTTP call for uncached points)."""
    out: dict[tuple[float, float], float | None] = {}
    need: list[tuple[float, float]] = []
    for lat, lon in coords:
        if use_cache:
            hit, sst = _cached(lat, lon)
            if hit:
                out[(lat, lon)] = sst
                continue
        need.append((lat, lon))
    if not need:
        return out

    data = _get(
        {
            "latitude": ",".join(str(p[0]) for p in need),
            "longitude": ",".join(str(p[1]) for p in need),
            "current": "sea_surface_temperature",
            "cell_selection": "sea",
        }
    )
    cache = _load() if use_cache else {}
    payloads: list[Any]
    if isinstance(data, list):
        payloads = list(data)
    elif data is not None:
        payloads = [data] * len(need)
    else:
        payloads = [None] * len(need)

    for i, point in enumerate(need):
        sst = _parse_sst(payloads[i]) if i < len(payloads) else None
        out[point] = sst
        if use_cache:
            _store(point[0], point[1], sst, cache)
    if use_cache:
        _save(cache)
    return out
