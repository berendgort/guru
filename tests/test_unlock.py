"""Claude + Codex/ChatGPT Work unlock -- only when blocked."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from guru.cli.main import app
from guru.core import config_io
from guru.core import unlock as unlock_mod
from guru.core import wire as wire_mod
from guru.core.unlock import (
    unlock_claude_network,
    unlock_codex_network,
    unlock_wind_charts,
)
from guru.core.wire import wire_codex


def test_unlock_skips_when_reachable(monkeypatch, tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(config_io, "home", lambda: home)
    monkeypatch.setattr(unlock_mod, "home", lambda: home)
    monkeypatch.setattr(
        "guru.core.path.probe_windguru",
        lambda: {"ok": True, "reachable": True, "host": "www.windguru.cz"},
    )
    result = unlock_wind_charts(wire=False)
    assert result["skipped"] is True
    assert result["reason"] == "already_reachable"
    assert not (home / ".claude" / "settings.json").exists()


def test_unlock_writes_claude_and_codex_when_blocked(monkeypatch, tmp_path: Path) -> None:
    home = tmp_path / "home"
    (home / ".codex").mkdir(parents=True)
    (home / ".codex" / "config.toml").write_text(
        'model = "gpt-5.4"\n\n[features]\nnetwork_proxy = true\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(config_io, "home", lambda: home)
    monkeypatch.setattr(unlock_mod, "home", lambda: home)
    monkeypatch.setattr(wire_mod, "home", lambda: home)
    monkeypatch.setattr(
        "guru.core.path.probe_windguru",
        lambda: {
            "ok": False,
            "reachable": False,
            "host": "www.windguru.cz",
            "error": "allowlist",
        },
    )
    monkeypatch.setattr(wire_mod, "resolve_guru_mcp", lambda: None)

    result = unlock_wind_charts(wire=False)
    assert result["skipped"] is False
    assert result["ok"] is True
    assert result["allowlist_written"] is True
    assert result["human_fix"]["id"] == "restart_after_unlock"
    assert "new chat" in result["say_to_rider"].lower()
    assert "settings hunt" in result["say_to_rider"].lower()
    assert result["rider_facing"]["kind"] == "user_visible_copy"
    assert result["rider_facing"]["text"] == result["say_to_rider"]
    assert "never /config" in result["agent_note"].lower()

    settings = json.loads((home / ".claude" / "settings.json").read_text())
    domains = settings["sandbox"]["network"]["allowedDomains"]
    assert "www.windguru.cz" in domains

    toml = (home / ".codex" / "config.toml").read_text()
    assert "features.network_proxy.domains" in toml
    assert "**.windguru.cz" in toml
    assert '"allow"' in toml


def test_codex_unlock_skips_without_codex_home(monkeypatch, tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(config_io, "home", lambda: home)
    monkeypatch.setattr(unlock_mod, "home", lambda: home)
    out = unlock_codex_network()
    assert out["skipped"] is True
    assert out["reason"] == "no_codex_home"


def test_claude_unlock_idempotent(monkeypatch, tmp_path: Path) -> None:
    home = tmp_path / "home"
    monkeypatch.setattr(config_io, "home", lambda: home)
    monkeypatch.setattr(unlock_mod, "home", lambda: home)
    first = unlock_claude_network()
    second = unlock_claude_network()
    assert first["changed"] is True
    assert second["changed"] is False


def test_wire_codex(monkeypatch, tmp_path: Path) -> None:
    home = tmp_path / "home"
    (home / ".codex").mkdir(parents=True)
    monkeypatch.setattr(config_io, "home", lambda: home)
    monkeypatch.setattr(wire_mod, "home", lambda: home)
    out = wire_codex("/tmp/guru-mcp")
    assert out["changed"] is True
    text = (home / ".codex" / "config.toml").read_text()
    assert "[mcp_servers.guru]" in text
    assert "/tmp/guru-mcp" in text


def test_cli_unlock_skip_json(monkeypatch, tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(config_io, "home", lambda: home)
    monkeypatch.setattr(unlock_mod, "home", lambda: home)
    monkeypatch.setattr(
        "guru.core.path.probe_windguru",
        lambda: {"ok": True, "reachable": True, "host": "www.windguru.cz"},
    )
    runner = CliRunner()
    result = runner.invoke(app, ["unlock", "--json"])
    assert result.exit_code == 0
    body = json.loads(result.stdout)
    assert body["ok"] is True
    assert body["data"]["skipped"] is True
