"""Spot resolve ambiguity."""

from __future__ import annotations

import pytest

from guru.models.forecast import Spot
from guru.search.exceptions import GuruAmbiguousError, GuruNotFoundError
from guru.search.spots import resolve_spot


def test_resolve_numeric(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "guru.search.spots.get_spot",
        lambda sid: Spot(id=sid, name="Castelldefels", country="Spain"),
    )
    spot = resolve_spot("201")
    assert spot.id == 201


def test_resolve_unique_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "guru.search.spots.search_spots",
        lambda q, limit=10: [Spot(id=201, name="Castelldefels", country="Spain")],
    )
    monkeypatch.setattr(
        "guru.search.spots.get_spot",
        lambda sid: Spot(id=sid, name="Castelldefels", country="Spain", lat=41.26, lon=1.95),
    )
    spot = resolve_spot("castelldefels")
    assert spot.id == 201
    assert spot.lat is not None


def test_resolve_ambiguous(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "guru.search.spots.search_spots",
        lambda q, limit=10: [
            Spot(id=1, name="slufter", country="Netherlands"),
            Spot(id=2, name="Slufter", country="Netherlands"),
        ],
    )
    with pytest.raises(GuruAmbiguousError) as exc:
        resolve_spot("slufter")
    assert len(exc.value.candidates) == 2


def test_resolve_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("guru.search.spots.search_spots", lambda q, limit=10: [])
    with pytest.raises(GuruNotFoundError):
        resolve_spot("zzzz-no-such-spot")


def test_resolve_pick(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "guru.search.spots.search_spots",
        lambda q, limit=10: [
            Spot(id=48309, name="De Slufter"),
            Spot(id=1, name="other"),
        ],
    )
    monkeypatch.setattr(
        "guru.search.spots.get_spot",
        lambda sid: Spot(id=sid, name="picked"),
    )
    spot = resolve_spot("slufter", pick=48309)
    assert spot.id == 48309


def test_resolve_pick_not_in_matches(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "guru.search.spots.search_spots",
        lambda q, limit=10: [Spot(id=1, name="other")],
    )
    with pytest.raises(GuruNotFoundError):
        resolve_spot("slufter", pick=48309)
