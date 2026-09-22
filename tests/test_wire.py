"""Auto-wire MCP config (no human steps)."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from guru.cli.main import app
from guru.core import config_io
from guru.core import wire as wire_mod
from guru.core.wire import wire_all, wire_status


def test_wire_writes_configs(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    (home / ".cursor").mkdir(parents=True)
    (home / ".config" / "Claude").mkdir(parents=True)
    monkeypatch.setattr(config_io, "home", lambda: home)
    monkeypatch.setattr(wire_mod, "home", lambda: home)

    mcp_bin = tmp_path / "guru-mcp"
    mcp_bin.write_text("#!/bin/sh\n", encoding="utf-8")
    mcp_bin.chmod(0o755)

    monkeypatch.setattr(
        wire_mod.shutil,
        "which",
        lambda name: str(mcp_bin) if name == "guru-mcp" else None,
    )

    result = wire_all(command=str(mcp_bin))
    assert result["ok"] is True
    cursor = json.loads((home / ".cursor" / "mcp.json").read_text())
    assert cursor["mcpServers"]["guru"]["command"] == str(mcp_bin)
    desktop = json.loads(
        (home / ".config" / "Claude" / "claude_desktop_config.json").read_text()
    )
    assert desktop["mcpServers"]["guru"]["command"] == str(mcp_bin)
    assert (home / ".claude.json").is_file()
    status = wire_status()
    assert status["ready"] is True


def test_cli_wire_status(monkeypatch, tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(config_io, "home", lambda: home)
    monkeypatch.setattr(wire_mod, "home", lambda: home)
    monkeypatch.setattr(wire_mod, "resolve_guru_mcp", lambda: None)
    runner = CliRunner()
    result = runner.invoke(app, ["wire", "--status", "--json"])
    assert result.exit_code == 0
    body = json.loads(result.stdout)
    assert body["ok"] is True
    assert body["data"]["ready"] is False
