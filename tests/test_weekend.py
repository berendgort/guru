"""Weekend report structure (offline, no network scan)."""

from __future__ import annotations

from guru.models.profile import RiderProfile, Sport
from guru.rider.weekend import _score


def test_weekend_score_prefers_go_nearby() -> None:
    assert _score("go", 20) > _score("go", 100)
    assert _score("go", 100) > _score("marginal", 20)


def test_range_ready() -> None:
    p = RiderProfile(
        sport=Sport.KITEFOIL,
        weight_kg=78,
        kites_m2=[9, 12],
        wetsuits=["3/2"],
        home_lat=41.39,
        home_lon=2.17,
        drive_km=200,
        range_label="Trabucador → Leucate",
    )
    assert p.is_ready()
    assert p.is_range_ready()
    bare = RiderProfile(
        sport=Sport.KITESURF, weight_kg=70, kites_m2=[10], wetsuits=["3/2"]
    )
    assert bare.missing_range_fields()
