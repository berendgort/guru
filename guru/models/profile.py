"""Rider profile — sport, weight, quiver, home range (no I/O)."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class Sport(str, Enum):
    KITESURF = "kitesurf"
    KITEFOIL = "kitefoil"
    SURFKITE = "surfkite"


class Level(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


_SPORT_ALIASES: dict[str, Sport] = {
    "kitesurf": Sport.KITESURF,
    "kite": Sport.KITESURF,
    "twintip": Sport.KITESURF,
    "tt": Sport.KITESURF,
    "kitefoil": Sport.KITEFOIL,
    "foil": Sport.KITEFOIL,
    "hydrofoil": Sport.KITEFOIL,
    "surfkite": Sport.SURFKITE,
    "surf": Sport.SURFKITE,
    "wave": Sport.SURFKITE,
}

_LEVEL_ALIASES: dict[str, Level] = {
    "beginner": Level.BEGINNER,
    "beg": Level.BEGINNER,
    "intermediate": Level.INTERMEDIATE,
    "int": Level.INTERMEDIATE,
    "advanced": Level.ADVANCED,
    "adv": Level.ADVANCED,
    "expert": Level.ADVANCED,
}


def parse_sport(raw: str | Sport) -> Sport:
    if isinstance(raw, Sport):
        return raw
    key = raw.strip().lower().replace(" ", "").replace("-", "").replace("_", "")
    for alias, sport in _SPORT_ALIASES.items():
        if key == alias.replace("-", "").replace("_", ""):
            return sport
    known = ", ".join(s.value for s in Sport)
    raise ValueError(f"Unknown sport {raw!r}. Choose: {known} (aliases: foil, twintip, wave)")


def parse_level(raw: str | Level) -> Level:
    if isinstance(raw, Level):
        return raw
    key = raw.strip().lower()
    if key in _LEVEL_ALIASES:
        return _LEVEL_ALIASES[key]
    known = ", ".join(level.value for level in Level)
    raise ValueError(f"Unknown level {raw!r}. Choose: {known}")


class RiderProfile(BaseModel):
    """Local rider prefs for gear advice + drive-range planning."""

    sport: Sport | None = None
    weight_kg: float | None = None
    level: Level | None = None  # required for advice — beginner/intermediate/advanced
    kites_m2: list[float] = Field(default_factory=list)
    boards: list[str] = Field(default_factory=list)
    wetsuits: list[str] = Field(default_factory=list)
    home_spots: list[int] = Field(default_factory=list)
    # Drive corridor (e.g. Barcelona home, Trabucador↔Leucate ≈ 180–200 km)
    home_lat: float | None = None
    home_lon: float | None = None
    drive_km: float | None = None
    range_label: str | None = None  # human note: "Trabucador → Leucate"
    session_hours: float = 3.0  # typical kite session 2–4 h

    @field_validator("weight_kg")
    @classmethod
    def _weight_ok(cls, v: float | None) -> float | None:
        if v is None:
            return None
        if v < 30 or v > 200:
            raise ValueError("weight_kg must be between 30 and 200")
        return float(v)

    @field_validator("session_hours")
    @classmethod
    def _session_ok(cls, v: float) -> float:
        if v < 1 or v > 6:
            raise ValueError("session_hours must be between 1 and 6")
        return float(v)

    @field_validator("drive_km")
    @classmethod
    def _drive_ok(cls, v: float | None) -> float | None:
        if v is None:
            return None
        if v < 5 or v > 500:
            raise ValueError("drive_km must be between 5 and 500")
        return float(v)

    @field_validator("kites_m2", mode="before")
    @classmethod
    def _sort_kites(cls, v: Any) -> list[float]:
        if not v:
            return []
        out = sorted({float(x) for x in v})
        for size in out:
            if size < 3 or size > 25:
                raise ValueError(f"kite size {size} m² out of range (3–25)")
        return out

    def missing_fields(self) -> list[str]:
        """Fields agents should collect via ``guru setup`` for gear advice."""
        missing: list[str] = []
        if self.sport is None:
            missing.append("sport")
        if self.weight_kg is None:
            missing.append("weight_kg")
        if self.level is None:
            missing.append("level")
        if not self.kites_m2:
            missing.append("kites_m2")
        if not self.wetsuits:
            missing.append("wetsuits")
        return missing

    def missing_range_fields(self) -> list[str]:
        """Needed for ``guru weekend`` / where-can-I-kite."""
        missing: list[str] = []
        if self.home_lat is None or self.home_lon is None:
            missing.append("home_lat/home_lon")
        if self.drive_km is None and not self.home_spots:
            missing.append("drive_km or home_spots")
        return missing

    def is_ready(self) -> bool:
        return not self.missing_fields()

    def is_range_ready(self) -> bool:
        return not self.missing_range_fields()

    def merge(self, **updates: Any) -> RiderProfile:
        data = self.model_dump()
        for key, value in updates.items():
            if value is None:
                continue
            data[key] = value
        return RiderProfile.model_validate(data)


class AdviceWindow(BaseModel):
    start: str
    end: str
    wind_kn: float
    gust_kn: float | None = None
    gust_spread_kn: float | None = None
    wind_quality: str | None = None  # smooth | ok | gusty
    kite_m2: float | None = None
    owned_kite_m2: float | None = None
    kite_gap_m2: float | None = None
    wetsuit: str | None = None
    owned_wetsuit: str | None = None
    accessories: list[str] = Field(default_factory=list)
    verdict: str  # go | marginal | no
    note: str = ""


class AdviceReport(BaseModel):
    verdict: str  # go | marginal | no | incomplete
    sport: str | None = None
    level: str | None = None
    model: str | None = None
    windows: list[AdviceWindow] = Field(default_factory=list)
    sizing_rule: str = "2.2*kg/kn; foil -40%; surfkite -15%; size for gusts"
    wetsuit_rule: str = (
        "kiteboarding air+wind-chill; warmer for 3–4h sessions / beginners"
    )
    checklist: list[str] = Field(default_factory=list)
    missing_profile: list[str] = Field(default_factory=list)
    summary: str = ""


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
    score: float = 0.0


class WeekendReport(BaseModel):
    verdict: str  # go | marginal | no | incomplete
    range_label: str | None = None
    home_lat: float | None = None
    home_lon: float | None = None
    drive_km: float | None = None
    spots: list[WeekendSpotAdvice] = Field(default_factory=list)
    missing_profile: list[str] = Field(default_factory=list)
    summary: str = ""
    thinking: list[str] = Field(default_factory=list)
