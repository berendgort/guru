"""WINDGURU DEFAULT Tune -- I/O orchestration over ``blend_math``."""

from __future__ import annotations

from typing import Any

from guru.models.blend import PRESET_WINDGURU_DEFAULT, BestForecast, BlendWeight
from guru.search.blend_math import (
    blend_from_forecast_spot,
    calc_sort_by_weights,
    weather_model_ids,
)
from guru.search.client import IAPI_CZ, get_client
from guru.search.forecast import get_forecast
from guru.search.spots import fetch_forecast_spot, spot_from_forecast_spot

__all__ = [
    "calc_sort_by_weights",
    "forecast_spot_raw",
    "get_best_forecast",
    "get_default_blend_settings",
    "list_spot_weather_models",
    "model_info_full",
    "rank_default_models",
]


def model_info_full() -> dict[str, Any]:
    return get_client().get_json(
        params={"q": "model_info_full"},
        referer="https://www.windguru.cz/",
        base=IAPI_CZ,
    )


def forecast_spot_raw(spot_id: int) -> dict[str, Any]:
    return fetch_forecast_spot(spot_id)


def get_default_blend_settings(
    data: dict[str, Any] | None = None,
    *,
    spot_id: int | None = None,
) -> dict[str, Any]:
    if data is None:
        if spot_id is None:
            raise ValueError("spot_id required when data is omitted")
        data = fetch_forecast_spot(spot_id)
    return blend_from_forecast_spot(data)


def list_spot_weather_models(
    data: dict[str, Any],
    model_info: dict[str, Any],
    *,
    spot_id: int | None = None,
) -> list[int]:
    if spot_id is None:
        spots = data.get("spots") or {}
        if not spots:
            raise ValueError("spot_id required when spots map is empty")
        spot_id = int(next(iter(spots.keys())))
    return weather_model_ids(spot_id, data, model_info)


def rank_default_models(
    spot_id: int,
    *,
    top: int = 3,
    forecast_spot: dict[str, Any] | None = None,
    model_info: dict[str, Any] | None = None,
) -> list[BlendWeight]:
    data = forecast_spot if forecast_spot is not None else fetch_forecast_spot(spot_id)
    info = model_info if model_info is not None else model_info_full()
    blend = blend_from_forecast_spot(data)
    model_ids = weather_model_ids(spot_id, data, info)
    return calc_sort_by_weights(model_ids, blend, info)[:top]


def get_best_forecast(
    spot_id: int,
    *,
    top: int = 3,
    hours: int | None = 48,
) -> BestForecast:
    """One ``forecast_spot`` + ``model_info_full``, then N model forecasts."""
    data = fetch_forecast_spot(spot_id)
    spot = spot_from_forecast_spot(data, spot_id)
    info = model_info_full()
    ranked = rank_default_models(
        spot_id, top=top, forecast_spot=data, model_info=info
    )
    forecasts = [
        get_forecast(spot_id, model=bw.id_model, hours=hours, spot=spot) for bw in ranked
    ]
    return BestForecast(
        spot=spot,
        preset=PRESET_WINDGURU_DEFAULT,
        models=ranked,
        forecasts=forecasts,
    )
