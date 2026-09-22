import pytest

from guru.search.forecast import get_forecast
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
