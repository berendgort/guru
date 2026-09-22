"""Offline forecast decode + envelope parity."""

from __future__ import annotations

import json
from pathlib import Path

from guru.core.envelope import API_VERSION, dump_model, error_payload, success_payload
from guru.models.forecast import Spot
from guru.search.exceptions import GuruAmbiguousError, GuruNotFoundError
from guru.search.forecast import decode_forecast

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_decode_forecast_gfs_201() -> None:
    data = json.loads((FIXTURES / "forecast_201_gfs.json").read_text())
    spot = Spot(id=201, name="Castelldefels", lat=41.26, lon=1.95)
    fc = decode_forecast(
        data, spot=spot, model_id=3, model_name="gfs", hours=12
    )
    assert fc.model_id == 3
    assert fc.spot.id == 201
    assert len(fc.hours) == 12
    assert fc.hours[0].wind_kn is not None
    dumped = dump_model(fc)
    assert dumped["model"] == "gfs"
    assert len(dumped["hours"]) == 12


def test_envelope_success_and_error() -> None:
    ok = success_payload({"x": 1})
    assert ok == {"ok": True, "api_version": API_VERSION, "data": {"x": 1}}

    err = error_payload(GuruNotFoundError("missing"))
    assert err["ok"] is False
    assert err["api_version"] == API_VERSION
    assert err["error_type"] == "not_found"
    assert err["retryable"] is False

    amb = error_payload(
        GuruAmbiguousError("a", candidates=[Spot(id=1, name="A"), Spot(id=2, name="B")])
    )
    assert amb["error_type"] == "ambiguous"
    assert len(amb["candidates"]) == 2
