"""Forecast fetch -- Windguru ``iapi.php?q=forecast``."""

from __future__ import annotations

__all__ = (
    "decode_forecast",
    "get_forecast",
)

from typing import Any

from guru.models.aliases import resolve_model
from guru.models.forecast import Forecast, ForecastHour, Spot, hour_time, init_to_datetime
from guru.models.rating import windguru_rating
from guru.search.client import IAPI_CZ, get_client
from guru.search.exceptions import GuruParseError
from guru.search.spots import get_spot


def get_forecast(
    spot_id: int,
    *,
    model: str | int = "gfs",
    hours: int | None = 48,
    spot: Spot | None = None,
) -> Forecast:
    """Fetch a forecast. ``hours`` truncates to the first N forecast *steps*."""
    model_id, model_name = resolve_model(model)
    resolved = spot if spot is not None else get_spot(spot_id)
    data = get_client().get_json(
        params={"q": "forecast", "id_spot": spot_id, "id_model": model_id},
        referer=f"https://www.windguru.cz/{spot_id}",
        base=IAPI_CZ,
    )
    return decode_forecast(
        data,
        spot=resolved,
        model_id=model_id,
        model_name=model_name,
        hours=hours,
    )


def decode_forecast(
    data: dict[str, Any],
    *,
    spot: Spot,
    model_id: int,
    model_name: str,
    hours: int | None,
) -> Forecast:
    """Pure decode of a ``q=forecast`` payload (fixture-friendly)."""
    fcst = data.get("fcst")
    if not isinstance(fcst, dict):
        raise GuruParseError(f"Missing fcst; keys={list(data.keys())}")

    init = init_to_datetime(fcst.get("initstamp"), fcst.get("initdate") or data.get("initdate"))
    hour_list = fcst.get("hours") or []
    wind = fcst.get("WINDSPD") or []
    gust = fcst.get("GUST") or []
    wdir = fcst.get("WINDDIR") or []
    tmp = fcst.get("TMP") or fcst.get("TMPE") or []
    apcp = fcst.get("APCP1") or fcst.get("APCP") or []
    tcdc = fcst.get("TCDC") or []
    rh = fcst.get("RH") or []

    rows: list[ForecastHour] = []
    for i, raw_h in enumerate(hour_list):
        h = int(raw_h)
        wind_kn = _num(wind, i)
        temp_c = _num(tmp, i)
        rating = windguru_rating(wind_kn, temp_c)
        rows.append(
            ForecastHour(
                hour=h,
                time=hour_time(init, h),
                wind_kn=wind_kn,
                gust_kn=_num(gust, i),
                wind_dir_deg=_num(wdir, i),
                temp_c=temp_c,
                precip_mm=_num(apcp, i),
                cloud_pct=_num(tcdc, i),
                rh_pct=_num(rh, i),
                rating_stars=rating.stars,
                rating_cold=rating.cold,
                rating=rating.label,
            )
        )
    if hours is not None:
        rows = rows[:hours]

    if spot.lat is None and data.get("lat") is not None:
        spot = spot.model_copy(
            update={
                "lat": float(data["lat"]),
                "lon": float(data["lon"]) if data.get("lon") is not None else None,
                "alt": float(data["alt"]) if data.get("alt") is not None else None,
            }
        )

    return Forecast(
        spot=spot,
        model=model_name,
        model_id=model_id,
        init=init,
        sunrise=data.get("sunrise"),
        sunset=data.get("sunset"),
        hours=rows,
    )


def _num(arr: list[Any], i: int) -> float | None:
    if i >= len(arr) or arr[i] is None or arr[i] == "":
        return None
    try:
        return float(arr[i])
    except (TypeError, ValueError):
        return None
