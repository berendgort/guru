"""Advice + weekend report models (no I/O)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AdviceWindow(BaseModel):
    start: str
    end: str
    wind_kn: float
    gust_kn: float | None = None
    gust_spread_kn: float | None = None
    wind_dir_deg: float | None = None
    wind_quality: str | None = None  # smooth | ok | gusty
    kite_m2: float | None = None
    owned_kite_m2: float | None = None
    kite_gap_m2: float | None = None
    wetsuit: str | None = None
    owned_wetsuit: str | None = None
    accessories: list[str] = Field(default_factory=list)
    verdict: str  # go | marginal | no
    rating_stars: int = 0
    rating_cold: bool = False
    rating: str = "-"
    note: str = ""
    hours_usable: float | None = None
    precip_mm: float | None = None
    sst_c: float | None = None
    shore_relation: str | None = None  # preferred | offshore | unknown
    hs_m: float | None = None
    period_s: float | None = None


class AdviceReport(BaseModel):
    verdict: str  # go | marginal | no | incomplete
    sport: str | None = None
    level: str | None = None
    model: str | None = None
    windows: list[AdviceWindow] = Field(default_factory=list)
    sizing_rule: str = "2.2*kg/kn; size for average; gusty -> warn"
    wetsuit_rule: str = (
        "SST base (Open-Meteo) else air+chill; ladder none|3/2|6/4|+jacket|+extremities"
    )
    checklist: list[str] = Field(default_factory=list)
    missing_profile: list[str] = Field(default_factory=list)
    summary: str = ""
    sst_c: float | None = None
    sst_source: str | None = None
    shore_source: str | None = None


class WeekendSpotAdvice(BaseModel):
    spot_id: int
    name: str
    lat: float | None = None
    lon: float | None = None
    drive_km: float | None = None
    verdict: str
    summary: str = ""
    best_window: AdviceWindow | None = None
    model: str | None = None
    model_agree: int = 1  # how many of top-3 models like this window's day
    score: float = 0.0
    sst_c: float | None = None


class ScheduleSlot(BaseModel):
    """Best call for a calendar day -- agents narrate the week without re-asking."""

    day: str  # YYYY-MM-DD (UTC)
    weekday: str  # Mon ... Sun
    start: str
    end: str
    spot_id: int
    name: str
    drive_km: float | None = None
    verdict: str
    wind_kn: float | None = None
    gust_kn: float | None = None
    wind_dir_deg: float | None = None
    owned_kite_m2: float | None = None
    owned_wetsuit: str | None = None
    model_agree: int = 1
    rating_stars: int = 0
    rating_cold: bool = False
    rating: str = "-"
    summary: str = ""
    hours_usable: float | None = None


class WeekendReport(BaseModel):
    verdict: str  # go | marginal | no | incomplete
    range_label: str | None = None
    home_lat: float | None = None
    home_lon: float | None = None
    drive_km: float | None = None
    hours: int = 96
    top_models: int = 3
    filter_day: str | None = None
    spots: list[WeekendSpotAdvice] = Field(default_factory=list)
    schedule: list[ScheduleSlot] = Field(default_factory=list)
    missing_profile: list[str] = Field(default_factory=list)
    summary: str = ""
    thinking: list[str] = Field(default_factory=list)
    sst_source: str | None = None


__all__ = [
    "AdviceReport",
    "AdviceWindow",
    "ScheduleSlot",
    "WeekendReport",
    "WeekendSpotAdvice",
]
