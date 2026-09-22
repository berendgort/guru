"""Auto-wire local STDIO ``guru-mcp`` into agent hosts (no human shell steps)."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from guru.core.config_io import home, read_json, read_toml, write_json, write_text_secure
from guru.core.toml_edit import upsert_toml_table

__all__ = (
    "resolve_guru_mcp",
    "wire_cursor",
    "wire_claude_desktop",
    "wire_claude_code",
    "wire_codex",
    "wire_all",
    "wire_status",
)


def resolve_guru_mcp() -> str | None:
    """Absolute path to ``guru-mcp`` (prefer stable pipx shim over ephemeral venv)."""
    pipx = home() / ".local" / "bin" / "guru-mcp"
    if pipx.is_file() and os.access(pipx, os.X_OK):
        return str(pipx.resolve())
    found = shutil.which("guru-mcp")
    if found:
        return str(Path(found).resolve())
    return None


def _merge_stdio_server(
    doc: dict[str, Any],
    *,
    command: str,
    key: str = "mcpServers",
) -> tuple[dict[str, Any], bool]:
    """Ensure ``guru`` STDIO entry under ``key``. Returns (doc, changed)."""
    servers = doc.get(key)
    if not isinstance(servers, dict):
        servers = {}
    entry = {"command": command}
    existing = servers.get("guru")
    if isinstance(existing, dict) and existing.get("command") == command:
        return doc, False
    servers["guru"] = entry
    doc[key] = servers
    return doc, True


def wire_cursor(command: str) -> dict[str, Any]:
    path = home() / ".cursor" / "mcp.json"
    doc = read_json(path)
    doc, changed = _merge_stdio_server(doc, command=command)
    if changed:
        write_json(path, doc)
    return {"target": "cursor", "path": str(path), "changed": changed, "ok": True}


def wire_claude_desktop(command: str) -> dict[str, Any]:
    candidates = [
        home() / ".config" / "Claude" / "claude_desktop_config.json",
        home()
        / "Library"
        / "Application Support"
        / "Claude"
        / "claude_desktop_config.json",
    ]
    appdata = os.environ.get("APPDATA")
    if appdata:
        candidates.append(Path(appdata) / "Claude" / "claude_desktop_config.json")

    path = next((p for p in candidates if p.parent.is_dir()), candidates[0])
    doc = read_json(path)
    doc, changed = _merge_stdio_server(doc, command=command)
    if changed:
        write_json(path, doc)
    return {"target": "claude_desktop", "path": str(path), "changed": changed, "ok": True}


def wire_claude_code(command: str) -> dict[str, Any]:
    """User-scope MCP in ``~/.claude.json`` and/or ``claude mcp add``."""
    path = home() / ".claude.json"
    claude_bin = shutil.which("claude")
    claude_cli: dict[str, Any] | None = None

    if claude_bin:
        try:
            proc = subprocess.run(
                [
                    claude_bin,
                    "mcp",
                    "add",
                    "--scope",
                    "user",
                    "--transport",
                    "stdio",
                    "guru",
                    "--",
                    command,
                ],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            out = (proc.stdout or "") + (proc.stderr or "")
            already = "already" in out.lower() or "exists" in out.lower()
            claude_cli = {
                "ok": proc.returncode == 0 or already,
                "exit_code": proc.returncode,
                "already": already,
                "output": out.strip()[:500],
            }
        except (OSError, subprocess.TimeoutExpired) as exc:
            claude_cli = {"ok": False, "error": str(exc)}

    doc = read_json(path)
    doc, changed = _merge_stdio_server(doc, command=command)
    if changed:
        write_json(path, doc)

    return {
        "target": "claude_code",
        "path": str(path),
        "changed": changed,
        "ok": True,
        "claude_cli": claude_cli,
    }


def wire_codex(command: str) -> dict[str, Any]:
    """Ensure ``[mcp_servers.guru]`` in ``~/.codex/config.toml``."""
    codex_home = home() / ".codex"
    path = codex_home / "config.toml"
    if not codex_home.is_dir() and not path.is_file():
        return {
            "target": "codex",
            "skipped": True,
            "reason": "no_codex_home",
            "ok": True,
        }
    raw = path.read_text(encoding="utf-8") if path.is_file() else ""
    new_text, changed = upsert_toml_table(
        raw,
        "mcp_servers.guru",
        {"command": command},
    )
    if changed:
        write_text_secure(path, new_text)
    return {
        "target": "codex",
        "path": str(path),
        "changed": changed,
        "ok": True,
    }


def wire_all(*, command: str | None = None) -> dict[str, Any]:
    """Wire Cursor + Claude Desktop + Claude Code. Agent runs this -- not the human."""
    cmd = command or resolve_guru_mcp()
    if not cmd:
        return {
            "ok": False,
            "error": "guru-mcp not found on PATH",
            "hint": "pipx install 'windguru[mcp]'",
            "wired": [],
        }

    results = [
        wire_cursor(cmd),
        wire_claude_desktop(cmd),
        wire_claude_code(cmd),
    ]
    return {
        "ok": True,
        "command": cmd,
        "mode": "stdio",
        "note": (
            "Local STDIO MCP runs on the user's machine with full network. "
            "Call wire ONLY when shell `guru` is unavailable and a local MCP host "
            "needs guru -- never every session. Prefer CLI."
        ),
        "wired": results,
        "restart_hint": (
            "Restart the MCP host once only if you just wired and tools are missing."
        ),
    }


def wire_status() -> dict[str, Any]:
    from guru.core.unlock import claude_wind_open, codex_wind_open

    cmd = resolve_guru_mcp()
    checks: list[dict[str, Any]] = []
    for label, path, key in (
        ("cursor", home() / ".cursor" / "mcp.json", "mcpServers"),
        (
            "claude_desktop",
            home() / ".config" / "Claude" / "claude_desktop_config.json",
            "mcpServers",
        ),
        ("claude_code", home() / ".claude.json", "mcpServers"),
    ):
        doc = read_json(path)
        servers = doc.get(key) if isinstance(doc.get(key), dict) else {}
        entry = servers.get("guru") if isinstance(servers, dict) else None
        present = isinstance(entry, dict) and bool(entry.get("command"))
        checks.append(
            {
                "target": label,
                "path": str(path),
                "present": present,
                "command": (entry or {}).get("command") if isinstance(entry, dict) else None,
            }
        )

    codex_path = home() / ".codex" / "config.toml"
    codex_doc = read_toml(codex_path)
    mcp_servers = (
        codex_doc.get("mcp_servers")
        if isinstance(codex_doc.get("mcp_servers"), dict)
        else {}
    )
    codex_entry = mcp_servers.get("guru") if isinstance(mcp_servers, dict) else None
    checks.append(
        {
            "target": "codex",
            "path": str(codex_path),
            "present": isinstance(codex_entry, dict) and bool(codex_entry.get("command")),
            "command": (
                codex_entry.get("command") if isinstance(codex_entry, dict) else None
            ),
        }
    )
    claude_open = claude_wind_open()
    codex_open = codex_wind_open()
    return {
        "guru_mcp": cmd,
        "ready": bool(cmd) and any(c["present"] for c in checks),
        "windguru_unlocked": claude_open or codex_open,
        "claude_unlocked": claude_open,
        "codex_unlocked": codex_open,
        "checks": checks,
    }
