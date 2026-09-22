"""First-pass intake parse + instruct wiring."""

from __future__ import annotations

from guru.rider.intake import parse_intake_text


def test_parse_intake_one_liner() -> None:
    raw = (
        "sport=kitefoil weight=78 level=intermediate kites=7,9,12 "
        "wetsuits=3/2,4/3 session=3 home=41.39,2.17 drive_km=200 "
        "range=Trabucador → Leucate"
    )
    out = parse_intake_text(raw)
    assert out["sport"] == "kitefoil"
    assert out["weight_kg"] == 78.0
    assert out["level"] == "intermediate"
    assert out["kites_m2"] == [7.0, 9.0, 12.0]
    assert out["wetsuits"] == ["3/2", "4/3"]
    assert out["session_hours"] == 3.0
    assert out["home_lat"] == 41.39
    assert out["home_lon"] == 2.17
    assert out["drive_km"] == 200.0
    assert "Trabucador" in out["range_label"]


def test_cli_setup_intake(tmp_path, monkeypatch) -> None:
    import json

    from typer.testing import CliRunner

    from guru.cli.main import app

    monkeypatch.setenv("GURU_CONFIG_DIR", str(tmp_path))
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "setup",
            "--intake",
            "sport=kitefoil weight=78 level=intermediate kites=7,9,12 wetsuits=3/2,4/3 "
            "session=3 home=41.39,2.17 drive_km=200 range=Trabucador → Leucate",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.stdout
    data = json.loads(result.stdout)["data"]
    assert data["ready"] is True
    assert data["range_ready"] is True
    assert data["first_pass"] is False


def test_instruct_includes_intake(tmp_path, monkeypatch) -> None:
    import json

    from typer.testing import CliRunner

    from guru.cli.main import app

    monkeypatch.setenv("GURU_CONFIG_DIR", str(tmp_path))
    runner = CliRunner()
    result = runner.invoke(app, ["instruct", "--json"])
    assert result.exit_code == 0
    body = json.loads(result.stdout)["data"]
    assert body["first_pass"] is True
    assert body["steps"][0]["action"] == "auto_upgrade"
    assert "prompt_to_user" in body["intake"]
    assert "level" in body["intake"]["prompt_to_user"].lower()
    assert "sport=" in body["intake"]["reply_template"]
    assert "level=" in body["intake"]["reply_template"]
    assert "level" in body["intake"]["required_highlights"]
    assert any(s["action"] == "first_pass_intake" for s in body["steps"])
