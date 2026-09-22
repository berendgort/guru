"""Blend / Tune weight models (WINDGURU DEFAULT)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from guru.models.forecast import Forecast, Spot

PRESET_WINDGURU_DEFAULT = "WINDGURU_DEFAULT"


class BlendWeight(BaseModel):
    id_model: int
    name: str
    weight: float
    weight_pct: float
    rank: int
    resolution_km: float | None = None
    initstamp: int | None = None


class BestForecast(BaseModel):
    """Top-N WINDGURU DEFAULT models + their forecasts for a spot."""

    spot: Spot
    preset: str = PRESET_WINDGURU_DEFAULT
    models: list[BlendWeight] = Field(default_factory=list)
    forecasts: list[Forecast] = Field(default_factory=list)
