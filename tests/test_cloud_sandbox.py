"""Simulate Claude Code cloud: allowlist written, HTTP still gated."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from guru.cli.main import app
from guru.core import config_io
from guru.core import unlock as unlock_mod
from guru.core import wire as wire_mod
from guru.core.hosts import WINDGURU_HOSTS
from guru.core.human_fix import pick_human_fix
from guru.core.path import probe_windguru
from guru.core.unlock import unlock_wind_charts
from guru.rider.instruct import instruct_payload
from guru.search.exceptions import GuruHTTPError


def _cloud_home(tmp_path: Path) -> Path:
    """Fake /root-style home with Claude allowlist already written."""
    home = tmp_path / "root"
    settings = home / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(
        json.dumps(
            {
                "sandbox": {
                    "network": {"allowedDomains": list(WINDGURU_HOSTS)},
                }
            }
        ),
        encoding="utf-8",
    )
    return home


def _gate_http(monkeypatch) -> None:
    """Every Windguru dial looks like Claude cloud allowlist 403."""

    class _Blocked:
        def get_json(self, **_kwargs):  # noqa: ANN003
            raise GuruHTTPError(
                "Windguru gated in this runtime (allowlist).",
                status_code=403,
            )

    monkeypatch.setattr("guru.search.client.get_client", lambda: _Blocked())


def _patch_homes(monkeypatch, home: Path) -> None:
    monkeypatch.setattr(config_io, "home", lambda: home)
    monkeypatch.setattr(unlock_mod, "home", lambda: home)
    monkeypatch.setattr(wire_mod, "home", lambda: home)


def test_cloud_probe_unlock_already_done_no_unlock_loop(
    monkeypatch, tmp_path: Path
) -> None:
    home = _cloud_home(tmp_path)
    _patch_homes(monkeypatch, home)
    _gate_http(monkeypatch)

    probe = probe_windguru()
    assert probe["reachable"] is False
    assert probe["unlock_already_done"] is True
    assert "unlock again" in probe["fix"].lower()
    assert "do not run unlock again" in probe["fix"].lower()
    assert "/config" in probe["fix"].lower()
    assert "never unlock again" in " ".join(probe["agent_must"]).lower()
    assert "run guru unlock again" in " ".join(probe["agent_must_not"]).lower()
    assert "jq" in " ".join(probe["agent_must_not"]).lower()


def test_cloud_unlock_returns_restart_not_config_domains(
    monkeypatch, tmp_path: Path
) -> None:
    home = _cloud_home(tmp_path)
    _patch_homes(monkeypatch, home)
    _gate_http(monkeypatch)
    monkeypatch.setattr(wire_mod, "resolve_guru_mcp", lambda: None)

    # Real probe (gated) for unlock's before/after checks.
    monkeypatch.setattr(
        "guru.core.path.probe_windguru",
        lambda: {
            "ok": False,
            "reachable": False,
            "unlock_already_done": True,
            "host": "www.windguru.cz",
        },
    )
    result = unlock_wind_charts(wire=False)
    assert result["allowlist_written"] is True
    assert result["still_blocked"] is True
    assert result["human_fix"]["id"] == "restart_after_unlock"
    assert "settings hunt" in result["say_to_rider"].lower()
    assert "/config" not in result["say_to_rider"].lower()
    assert "allowed domains" not in result["say_to_rider"].lower()


def test_cloud_agent_recipe_after_new_chat_is_cursor() -> None:
    recipe = pick_human_fix(still_blocked=True, allowlist_written=True)
    assert recipe is not None
    assert recipe["id"] == "fallback_cursor"
    assert "cursor" in recipe["say_to_rider"].lower()
    assert "allowed domains" not in recipe["say_to_rider"].lower()


def test_cloud_instruct_forbids_config_when_unlocked(
    monkeypatch, tmp_path: Path
) -> None:
    home = _cloud_home(tmp_path)
    _patch_homes(monkeypatch, home)
    _gate_http(monkeypatch)
    monkeypatch.setattr(
        "guru.rider.instruct.profile_payload",
        lambda *_a, **_k: {
            "ready": True,
            "range_ready": True,
            "first_pass": False,
        },
    )
    monkeypatch.setattr(
        "guru.rider.instruct.load_profile",
        lambda: object(),
    )
    monkeypatch.setattr(
        "guru.rider.instruct.upgrade_status",
        lambda: {"installed": "0.3.24", "update_available": False},
    )

    payload = instruct_payload()
    assert payload["network"]["unlock_already_done"] is True
    assert payload["on_unreachable"]["active"] is True
    do_not = " ".join(payload["on_unreachable"]["do_not"]).lower()
    assert "unlock again" in do_not
    assert "/config" in do_not
    do = " ".join(payload["on_unreachable"]["do"]).lower()
    assert "fallback_cursor" in do
    assert "jq" in do_not or "jq" in do


def test_cloud_weekend_json_includes_rider_facing(
    monkeypatch, tmp_path: Path
) -> None:
    """guru weekend --json must ship restart copy, not invent /config."""
    home = _cloud_home(tmp_path)
    _patch_homes(monkeypatch, home)
    _gate_http(monkeypatch)

    runner = CliRunner()
    result = runner.invoke(app, ["weekend", "--json"])
    assert result.exit_code != 0
    body = json.loads(result.stdout)
    assert body["ok"] is False
    assert body["error_type"] == "network_gated"
    assert body["network"]["unlock_already_done"] is True
    assert body["human_fix"]["id"] == "restart_after_unlock"
    assert body["rider_facing"]["kind"] == "user_visible_copy"
    assert "new chat" in body["rider_facing"]["text"].lower()
    assert "settings hunt" in body["say_to_rider"].lower()
    assert "/config" not in body["say_to_rider"].lower()
    assert "allowed domains" not in body["say_to_rider"].lower()
    assert "never_unlock_again" in body["agent_next"]


def test_cloud_weekend_before_unlock_tells_agent_to_unlock(
    monkeypatch, tmp_path: Path
) -> None:
    home = tmp_path / "root"
    home.mkdir()
    _patch_homes(monkeypatch, home)
    _gate_http(monkeypatch)

    runner = CliRunner()
    result = runner.invoke(app, ["weekend", "--json"])
    assert result.exit_code != 0
    body = json.loads(result.stdout)
    assert body["ok"] is False
    assert body["error_type"] == "network_gated"
    assert body["network"]["unlock_already_done"] is False
    assert body["rider_facing"] is None
    assert "run_guru_unlock_json_once" in body["agent_next"]


def test_cloud_doctor_json_marks_unlocked_but_unreachable(
    monkeypatch, tmp_path: Path
) -> None:
    home = _cloud_home(tmp_path)
    _patch_homes(monkeypatch, home)
    _gate_http(monkeypatch)

    runner = CliRunner()
    result = runner.invoke(app, ["doctor", "--json"])
    assert result.exit_code == 0
    body = json.loads(result.stdout)
    assert body["ok"] is True
    net = body["data"]["network"]
    assert net["reachable"] is False
    assert net["unlock_already_done"] is True
    assert body["data"]["mcp_wire"]["claude_unlocked"] is True
    assert body["data"]["mcp_wire"]["windguru_unlocked"] is True
    assert "do not run unlock again" in net["fix"].lower()
