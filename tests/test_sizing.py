"""Offline kite / wetsuit sizing."""

from __future__ import annotations

from guru.models.profile import Level, Sport
from guru.rider.sizing import (
    hour_verdict,
    ideal_kite_m2,
    min_wind_kn,
    pick_owned_kite,
    pick_owned_wetsuit,
    recommend_wetsuit,
)


def test_ideal_kite_75kg_15kt() -> None:
    assert ideal_kite_m2(75, 15, sport=Sport.KITESURF) == 11.0


def test_foil_smaller_than_twintip() -> None:
    tt = ideal_kite_m2(75, 15, sport=Sport.KITESURF)
    foil = ideal_kite_m2(75, 15, sport=Sport.KITEFOIL)
    assert tt is not None and foil is not None
    assert foil < tt
    assert abs(foil - tt * 0.6) < 0.6


def test_surfkite_slightly_smaller() -> None:
    tt = ideal_kite_m2(75, 18, sport=Sport.KITESURF)
    surf = ideal_kite_m2(75, 18, sport=Sport.SURFKITE)
    assert tt is not None and surf is not None
    assert surf <= tt


def test_size_for_average_not_gusts() -> None:
    calm = ideal_kite_m2(75, 18, gust_kn=18)
    gusty = ideal_kite_m2(75, 18, gust_kn=28)
    assert calm is not None and gusty is not None
    assert gusty == calm


def test_pick_owned_kite() -> None:
    owned, gap = pick_owned_kite(10.5, [7, 9, 12])
    assert owned == 9
    assert gap is not None
    assert abs(gap - (9 - 10.5)) < 0.01


def test_wetsuit_ladder_calm_2h() -> None:
    assert recommend_wetsuit(26, wind_kn=8, session_hours=2)[0] == "none"
    assert recommend_wetsuit(18, wind_kn=8, session_hours=2)[0] == "3/2"
    assert recommend_wetsuit(12, wind_kn=8, session_hours=2)[0] == "6/4"
    assert recommend_wetsuit(7, wind_kn=8, session_hours=2)[0] == "6/4+jacket"
    assert recommend_wetsuit(2, wind_kn=8, session_hours=2)[0] == "6/4+jacket+gloves+boots"


def test_wetsuit_warmer_for_long_windy_session() -> None:
    calm_short, _ = recommend_wetsuit(
        16, wind_kn=8, session_hours=2, level=Level.INTERMEDIATE
    )
    long_windy, acc = recommend_wetsuit(
        16, wind_kn=20, session_hours=4, level=Level.BEGINNER
    )
    assert calm_short == "3/2"
    assert long_windy in {"6/4", "6/4+jacket", "6/4+jacket+gloves+boots"}
    assert "jacket" in long_windy or "gloves" in acc or long_windy.startswith("6")


def test_pick_owned_wetsuit() -> None:
    assert pick_owned_wetsuit("3/2", ["6/4", "3/2"]) == "3/2"
    assert pick_owned_wetsuit("6/4", ["3/2", "6/4"]) == "6/4"
    assert pick_owned_wetsuit("6/4+jacket", ["3/2", "6/4"]) == "6/4"


def test_min_wind_foil_lower() -> None:
    assert min_wind_kn(Sport.KITEFOIL, Level.INTERMEDIATE) < min_wind_kn(
        Sport.KITESURF, Level.INTERMEDIATE
    )


def test_intermediate_twintip_floor_13() -> None:
    assert min_wind_kn(Sport.KITESURF, Level.INTERMEDIATE) == 13.0


def test_expert_lower_than_advanced() -> None:
    assert min_wind_kn(Sport.KITESURF, Level.EXPERT) < min_wind_kn(
        Sport.KITESURF, Level.ADVANCED
    )


def test_hour_verdict() -> None:
    assert hour_verdict(6, 8, sport=Sport.KITESURF, level=Level.INTERMEDIATE) == "no"
    assert hour_verdict(14, 16, sport=Sport.KITESURF, level=Level.INTERMEDIATE) == "go"
    # Gusty: warn, still GO for intermediate (beginners stay marginal)
    assert hour_verdict(14, 24, sport=Sport.KITESURF, level=Level.INTERMEDIATE) == "go"
    assert (
        hour_verdict(14, 24, sport=Sport.KITESURF, level=Level.BEGINNER) == "marginal"
    )
    assert hour_verdict(10, 12, sport=Sport.KITEFOIL, level=Level.INTERMEDIATE) == "go"
