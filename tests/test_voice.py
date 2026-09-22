"""Kite-bro voice helpers."""

from __future__ import annotations

from guru.rider.voice import CALL, call_label, voice_payload


def test_call_labels() -> None:
    assert call_label("go") == "SEND IT"
    assert call_label("marginal") == "SOFT CALL"
    assert call_label("no") == "SIT IT OUT"
    assert set(CALL) >= {"go", "marginal", "no", "incomplete"}


def test_voice_payload_has_vocab() -> None:
    payload = voice_payload()
    assert payload["id"] == "kite_bro"
    assert "send it" in payload["vocab"]
    assert "SEND IT" in payload["rule"]
