"""Profile store round-trip under GURU_CONFIG_DIR."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from guru.models.profile import Level, Sport, parse_sport
from guru.rider import profile_store


def test_parse_sport_aliases() -> None:
    assert parse_sport("foil") is Sport.KITEFOIL
    assert parse_sport("twintip") is Sport.KITESURF
    assert parse_sport("wave") is Sport.SURFKITE


def test_profile_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GURU_CONFIG_DIR", str(tmp_path))
    assert not profile_store.load_profile().is_ready()

    saved = profile_store.update_profile(
        sport="kitefoil",
        weight_kg=78,
        level="intermediate",
        kites_m2=[12, 7, 9],
        wetsuits=["3/2", "4/3"],
        boards=["foil 1300"],
    )
    assert saved.sport is Sport.KITEFOIL
    assert saved.kites_m2 == [7.0, 9.0, 12.0]
    assert saved.is_ready()

    path = profile_store.profile_path()
    assert path.is_file()
    raw = json.loads(path.read_text())
    assert raw["weight_kg"] == 78

    loaded = profile_store.load_profile()
    assert loaded.level is Level.INTERMEDIATE
    payload = profile_store.profile_payload(loaded)
    assert payload["ready"] is True
    assert payload["missing"] == []


def test_profile_merge(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GURU_CONFIG_DIR", str(tmp_path))
    profile_store.update_profile(sport="kitesurf", weight_kg=70)
    profile_store.update_profile(kites_m2=[10, 13], wetsuits=["shorty"])
    p = profile_store.load_profile()
    assert p.sport is Sport.KITESURF
    assert p.weight_kg == 70
    assert p.kites_m2 == [10.0, 13.0]
