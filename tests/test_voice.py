"""Kite-bro / programmer-guru voice helpers."""

from __future__ import annotations

from guru.rider.voice import (
    CALL,
    NAME_LORE,
    call_label,
    joke,
    tagline,
    voice_payload,
)


def test_call_labels() -> None:
    assert call_label("go") == "SEND IT"
    assert call_label("marginal") == "SOFT CALL"
    assert call_label("no") == "SIT IT OUT"
    assert set(CALL) >= {"go", "marginal", "no", "incomplete"}


def test_voice_payload_has_vocab_lore_jokes() -> None:
    payload = voice_payload()
    assert payload["id"] == "kite_bro"
    assert "send it" in payload["vocab"]
    assert "SEND IT" in payload["rule"]
    assert "Wind + Guru" in payload["lore"]["windguru"]
    assert "guru_cli" in payload["lore"]
    assert payload["jokes"]["general"]
    assert "programmer" in payload["style"]


def test_joke_and_tagline_stable() -> None:
    assert joke(seed="x") == joke(seed="x")
    assert tagline(seed="y") == tagline(seed="y")
    assert "Wind" in NAME_LORE["windguru"] or "Guru" in NAME_LORE["windguru"]
