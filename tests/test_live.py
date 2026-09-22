import pytest

from guru.search.blend import get_best_forecast, rank_default_models
from guru.search.forecast import get_forecast
from guru.search.near import spots_near
from guru.search.spots import search_spots


@pytest.mark.live
def test_search_castelldefels() -> None:
    spots = search_spots("castelldefels", limit=5)
    assert spots
    assert any(s.id == 201 for s in spots)


@pytest.mark.live
def test_forecast_201() -> None:
    fc = get_forecast(201, model="gfs", hours=12)
    assert fc.spot.id == 201
    assert len(fc.hours) == 12
    assert fc.hours[0].wind_kn is not None


@pytest.mark.live
def test_best_201_top3() -> None:
    ranked = rank_default_models(201, top=3)
    assert len(ranked) == 3
    assert ranked[0].weight >= ranked[1].weight
    best = get_best_forecast(201, top=3, hours=6)
    assert len(best.forecasts) == 3


@pytest.mark.live
def test_near_nl_coast() -> None:
    spots = spots_near(51.9, 4.1, radius_km=40, limit=5)
    assert spots
    assert spots[0].lat is not None
