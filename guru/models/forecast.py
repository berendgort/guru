"""Pydantic models."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, Field


class Spot(BaseModel):
    id: int
    name: str
    country: str | None = None
    nickname: str | None = None
    lat: float | None = None
    lon: float | None = None
    alt: float | None = None


class ForecastHour(BaseModel):
    hour: int
    time: datetime
    wind_kn: float | None = None
    gust_kn: float | None = None
    wind_dir_deg: float | None = None
    temp_c: float | None = None
    precip_mm: float | None = None
    cloud_pct: float | None = None
    rh_pct: float | None = None


class Forecast(BaseModel):
    spot: Spot
    model: str
    model_id: int
    init: datetime | None = None
    sunrise: str | None = None
    sunset: str | None = None
    hours: list[ForecastHour] = Field(default_factory=list)


def wind_dir_cardinal(deg: float | None) -> str:
    if deg is None:
        return "-"
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return dirs[int((deg + 22.5) % 360 // 45)]


def init_to_datetime(initstamp: int | None, initdate: str | None) -> datetime | None:
    if initstamp:
        return datetime.fromtimestamp(int(initstamp), tz=timezone.utc)
    if initdate:
        try:
            return datetime.strptime(initdate, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def hour_time(init: datetime | None, hour: int) -> datetime:
    base = init or datetime.now(tz=timezone.utc)
    return base + timedelta(hours=hour)
