"""Free Windguru wave forecast (surfkite annotate only)."""

from __future__ import annotations

from typing import Any

from guru.models.forecast import Forecast
from guru.search.client import IAPI_CZ, get_client
from guru.search.exceptions import GuruParseError
from guru.search.spots import fetch_forecast_spot

__all__ = (
    "FREE_WAVE_MODELS",
    "decode_wave_series",
    "fetch_wave_raw",
    "resolve_wave_model_id",
    "wave_map_for_forecast",
)

FREE_WAVE_MODELS = {83, 84, 85, 118, 60}


def resolve_wave_model_id(
    spot_id: int, forecast_spot: dict[str, Any] | None = None
) -> int | None:
    data = forecast_spot if forecast_spot is not None else fetch_forecast_spot(spot_id)
    for tab in data.get("tabs") or []:
        wid = tab.get("id_model_wave")
        if wid is None:
            continue
        mid = int(wid)
        if mid in FREE_WAVE_MODELS:
            return mid
    return None


def fetch_wave_raw(
    spot_id: int, *, wave_model_id: int | None = None
) -> dict[str, Any] | None:
    mid = wave_model_id or resolve_wave_model_id(spot_id)
    if mid is None:
        return None
    return get_client().get_json(
        params={"q": "forecast", "id_spot": spot_id, "id_model": mid},
        referer=f"https://www.windguru.cz/{spot_id}",
        base=IAPI_CZ,
    )


def decode_wave_series(
    data: dict[str, Any],
) -> list[tuple[float | None, float | None]]:
    """Per-hour (hs_m, period_s)."""
    fcst = data.get("fcst")
    if not isinstance(fcst, dict):
        raise GuruParseError("wave fcst missing")
    n = len(fcst.get("hours") or [])
    hs = fcst.get("HTSGW") or []
    per = fcst.get("PERPW") or fcst.get("SWPER1") or []
    return [(_num(hs, i), _num(per, i)) for i in range(n)]


def wave_map_for_forecast(
    forecast: Forecast,
) -> dict[int, tuple[float | None, float | None]] | None:
    """Best-effort free-wave series keyed by Windguru hour index."""
    try:
        raw = fetch_wave_raw(forecast.spot.id)
        if raw is None:
            return None
        series = decode_wave_series(raw)
        out: dict[int, tuple[float | None, float | None]] = {}
        for i, hour in enumerate(forecast.hours):
            if i < len(series):
                out[int(hour.hour)] = series[i]
        return out or None
    except Exception:  # noqa: BLE001
        return None


def _num(arr: list[Any], i: int) -> float | None:
    if i >= len(arr) or arr[i] is None or arr[i] == "":
        return None
    try:
        return float(arr[i])
    except (TypeError, ValueError):
        return None
