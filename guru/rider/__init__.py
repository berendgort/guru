"""Rider advice package."""

from guru.rider.advice import advise_forecast
from guru.rider.profile_store import (
    load_profile,
    profile_payload,
    update_profile,
)
from guru.rider.sizing import ideal_kite_m2, pick_owned_kite, recommend_wetsuit
from guru.rider.weekend import scan_weekend

__all__ = [
    "advise_forecast",
    "ideal_kite_m2",
    "load_profile",
    "pick_owned_kite",
    "profile_payload",
    "recommend_wetsuit",
    "scan_weekend",
    "update_profile",
]
