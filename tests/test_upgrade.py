"""Upgrade / version compare helpers."""

from __future__ import annotations

from guru.core.upgrade import is_newer, upgrade_status


def test_is_newer() -> None:
    assert is_newer("0.3.11", "0.3.10")
    assert not is_newer("0.3.10", "0.3.11")
    assert not is_newer("0.3.11", "0.3.11")
    assert is_newer("1.0.0", "0.9.9")


def test_upgrade_status_no_downgrade(monkeypatch) -> None:
    monkeypatch.setattr("guru.core.upgrade._installed_version", lambda: "0.3.11")
    monkeypatch.setattr("guru.core.upgrade.pypi_latest_version", lambda: "0.3.10")
    status = upgrade_status()
    assert status["update_available"] is False
    assert status["installed"] == "0.3.11"
    assert status["pypi_latest"] == "0.3.10"
