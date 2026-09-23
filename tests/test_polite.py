"""Polite Windguru client: spacing, cache, IP-Forbidden circuit."""

from __future__ import annotations

import time
from typing import Any

import pytest

from guru.core.errors import classify_error
from guru.search.client import Client
from guru.search.exceptions import GuruHTTPError
from guru.search.polite import (
    cache_get,
    cache_key,
    cache_set,
    check_circuit,
    is_ip_forbidden,
    reset_polite,
    trip_circuit,
    wait_turn,
)


@pytest.fixture(autouse=True)
def _clean_polite() -> None:
    reset_polite()
    yield
    reset_polite()


def test_is_ip_forbidden_vs_allowlist() -> None:
    ban = "FORBIDDEN\nYou do not have permission to access windguru.cz\nProvide your IP"
    assert is_ip_forbidden(403, ban) is True
    assert is_ip_forbidden(403, "domain not on allowlist") is False
    assert is_ip_forbidden(429, ban) is False


def test_wait_turn_enforces_min_interval() -> None:
    t0 = time.monotonic()
    wait_turn(min_interval=0.15)
    wait_turn(min_interval=0.15)
    assert time.monotonic() - t0 >= 0.14


def test_cache_round_trip() -> None:
    key = cache_key("https://example", {"q": "forecast", "id_spot": 1})
    assert cache_get(key) is None
    cache_set(key, {"ok": True}, ttl=60)
    assert cache_get(key) == {"ok": True}


def test_cache_evicts_at_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("guru.search.polite.CACHE_MAX", 2)
    reset_polite()
    cache_set("a", 1, ttl=60)
    cache_set("b", 2, ttl=60)
    cache_set("c", 3, ttl=60)
    assert cache_get("a") is None
    assert cache_get("b") == 2
    assert cache_get("c") == 3


def test_circuit_blocks_after_trip() -> None:
    trip_circuit(ttl=60)
    with pytest.raises(GuruHTTPError) as ei:
        check_circuit()
    assert ei.value.status_code == 403
    cls = classify_error(ei.value)
    assert cls.error_type == "rate_limited"
    assert cls.retryable is False


def test_client_caches_and_trips_on_forbidden(monkeypatch: pytest.MonkeyPatch) -> None:
    client = Client()
    calls = {"n": 0}

    class _Resp:
        def __init__(self, status: int, text: str, payload: Any = None) -> None:
            self.status_code = status
            self.text = text
            self._payload = payload

        def json(self) -> Any:
            return self._payload

    def fake_get(*_a: Any, **_k: Any) -> _Resp:
        calls["n"] += 1
        if calls["n"] == 1:
            return _Resp(200, "{}", {"fcst": {"ok": 1}})
        return _Resp(
            403,
            "FORBIDDEN You do not have permission to access windguru.cz",
        )

    monkeypatch.setattr(client._session, "get", fake_get)
    monkeypatch.setattr("guru.search.polite.MIN_INTERVAL", 0.0)
    reset_polite()

    a = client.get_json(
        params={"q": "forecast", "id_spot": 1},
        referer="https://www.windguru.cz/1",
    )
    b = client.get_json(
        params={"q": "forecast", "id_spot": 1},
        referer="https://www.windguru.cz/1",
    )
    assert a == b == {"fcst": {"ok": 1}}
    assert calls["n"] == 1  # second was cache

    with pytest.raises(GuruHTTPError):
        client.get_json(
            params={"q": "forecast", "id_spot": 2},
            referer="https://www.windguru.cz/2",
        )
    assert calls["n"] == 2
    with pytest.raises(GuruHTTPError) as ei:
        client.get_json(
            params={"q": "forecast", "id_spot": 3},
            referer="https://www.windguru.cz/3",
        )
    assert "circuit" in str(ei.value).lower()
    assert calls["n"] == 2  # circuit stopped further dials


def test_classify_ip_forbidden_message() -> None:
    err = GuruHTTPError(
        "Windguru Forbidden (IP ban / anti-scrape). circuit open.",
        status_code=403,
    )
    cls = classify_error(err)
    assert cls.error_type == "rate_limited"
    assert cls.retryable is False


def test_get_best_forecast_reuses_model_info(monkeypatch: pytest.MonkeyPatch) -> None:
    from guru.models.blend import BlendWeight
    from guru.models.forecast import Forecast, Spot
    from guru.search import blend as blend_mod

    info_calls = {"n": 0}

    def fake_info() -> dict[str, Any]:
        info_calls["n"] += 1
        return {"models": {}}

    monkeypatch.setattr(blend_mod, "model_info_full", fake_info)
    monkeypatch.setattr(
        blend_mod,
        "fetch_forecast_spot",
        lambda _sid: {"spots": {"1": {"id_spot": 1, "spotname": "T"}}},
    )
    monkeypatch.setattr(
        blend_mod,
        "rank_default_models",
        lambda *_a, **_k: [
            BlendWeight(
                id_model=3, name="gfs", weight=1.0, weight_pct=100.0, rank=1
            )
        ],
    )
    monkeypatch.setattr(
        blend_mod,
        "get_forecast",
        lambda *_a, **_k: Forecast(
            spot=Spot(id=1, name="T"),
            model="gfs",
            model_id=3,
            init=None,
            hours=[],
        ),
    )
    shared = {"shared": True}
    blend_mod.get_best_forecast(1, top=1, model_info=shared)
    blend_mod.get_best_forecast(1, top=1, model_info=shared)
    assert info_calls["n"] == 0
    blend_mod.get_best_forecast(1, top=1)
    assert info_calls["n"] == 1
