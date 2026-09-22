"""Windguru star rating (site-default thresholds)."""

from __future__ import annotations

from guru.models.rating import windguru_rating


def test_rating_thresholds() -> None:
    assert windguru_rating(10.5).stars == 0
    assert windguru_rating(10.6).stars == 1
    assert windguru_rating(15.5).stars == 1
    assert windguru_rating(15.6).stars == 2
    assert windguru_rating(19.3).stars == 2
    assert windguru_rating(19.4).stars == 3
    assert windguru_rating(25.0).stars == 3


def test_rating_cold_blue_stars() -> None:
    warm = windguru_rating(16.0, 18.0)
    assert warm.stars == 2
    assert warm.cold is False
    assert warm.label == "★★"

    cold = windguru_rating(16.0, 9.0)
    assert cold.stars == 2
    assert cold.cold is True
    assert cold.label == "★★ cold"

    assert windguru_rating(8.0, 5.0).label == "-"


def test_decode_forecast_includes_rating() -> None:
    import json
    from pathlib import Path

    from guru.models.forecast import Spot
    from guru.search.forecast import decode_forecast

    data = json.loads(
        (Path(__file__).resolve().parents[1] / "fixtures" / "forecast_201_gfs.json").read_text()
    )
    fc = decode_forecast(
        data, spot=Spot(id=201, name="Castelldefels"), model_id=3, model_name="gfs", hours=12
    )
    assert fc.hours
    assert hasattr(fc.hours[0], "rating_stars")
    assert fc.hours[0].rating  # "—" or stars
