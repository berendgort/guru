"""Offline advice engine over fixture forecast + sample profile."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from guru.cli.main import app
from guru.models.forecast import Spot
from guru.models.profile import Level, RiderProfile, Sport
from guru.rider.advice import advise_forecast
from guru.search.forecast import decode_forecast

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_advice_incomplete_without_profile() -> None:
    data = json.loads((FIXTURES / "forecast_201_gfs.json").read_text())
    spot = Spot(id=201, name="Castelldefels")
    fc = decode_forecast(data, spot=spot, model_id=3, model_name="gfs", hours=24)
    report = advise_forecast(fc, RiderProfile())
    assert report.verdict == "incomplete"
    assert "sport" in report.missing_profile
    assert "weight_kg" in report.missing_profile
    assert "level" in report.missing_profile


def test_advice_foil_windows_from_fixture() -> None:
    data = json.loads((FIXTURES / "forecast_201_gfs.json").read_text())
    spot = Spot(id=201, name="Castelldefels")
    fc = decode_forecast(data, spot=spot, model_id=3, model_name="gfs", hours=48)
    profile = RiderProfile(
        sport=Sport.KITEFOIL,
        weight_kg=78,
        level=Level.INTERMEDIATE,
        kites_m2=[7, 9, 12],
        wetsuits=["3/2", "4/3"],
    )
    report = advise_forecast(fc, profile)
    assert report.verdict in {"go", "marginal", "no"}
    assert report.missing_profile == []
    assert report.sport == "kitefoil"
    assert "foil" in report.sizing_rule
    if report.windows:
        w = report.windows[0]
        assert w.owned_kite_m2 in {7.0, 9.0, 12.0}
        assert w.verdict in {"go", "marginal"}


def test_cli_setup_and_instruct(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GURU_CONFIG_DIR", str(tmp_path))
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "setup",
            "--sport",
            "kitefoil",
            "--weight",
            "78",
            "--level",
            "intermediate",
            "--kites",
            "7,9,12",
            "--wetsuits",
            "3/2,4/3",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["data"]["ready"] is True

    instruct = runner.invoke(app, ["instruct", "--json"])
    assert instruct.exit_code == 0
    body = json.loads(instruct.stdout)["data"]
    assert body["steps"][0]["action"] == "auto_upgrade"
    assert "upgrade" in body
    assert "upgrade_commands" in body["upgrade"]
    assert any(s.get("action") == "first_pass_intake" for s in body["steps"])
    assert "intake" in body
    assert any(
        s.get("action") == "weekend_or_best"
        or "weekend" in (s.get("command") or "")
        for s in body["steps"]
    )
