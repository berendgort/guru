"""Auto-wire local STDIO ``guru-mcp`` into agent hosts — no human shell steps."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


def _home() -> Path:
    return Path.home()


def resolve_guru_mcp() -> str | None:
    """Absolute path to ``guru-mcp`` (prefer stable pipx shim over ephemeral venv)."""
    pipx = _home() / ".local" / "bin" / "guru-mcp"
    if pipx.is_file() and os.access(pipx, os.X_OK):
        return str(pipx.resolve())
    found = shutil.which("guru-mcp")
    if found:
        return str(Path(found).resolve())
    return None


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass


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
    if existing == entry or (
        isinstance(existing, dict)
        and existing.get("command") == command
        and not existing.get("args")
    ):
        # Already correct (allow extra keys like type/env as long as command matches)
        if isinstance(existing, dict) and existing.get("command") == command:
            return doc, False
    servers["guru"] = entry
    doc[key] = servers
    return doc, True


def wire_cursor(command: str) -> dict[str, Any]:
    path = _home() / ".cursor" / "mcp.json"
    doc = _read_json(path)
    doc, changed = _merge_stdio_server(doc, command=command)
    if changed:
        _write_json(path, doc)
    return {"target": "cursor", "path": str(path), "changed": changed, "ok": True}


def wire_claude_desktop(command: str) -> dict[str, Any]:
    # Linux; macOS uses ~/Library/Application Support/Claude/
    candidates = [
        _home() / ".config" / "Claude" / "claude_desktop_config.json",
        _home()
        / "Library"
        / "Application Support"
        / "Claude"
        / "claude_desktop_config.json",
    ]
    appdata = os.environ.get("APPDATA")
    if appdata:
        candidates.append(Path(appdata) / "Claude" / "claude_desktop_config.json")

    path = next((p for p in candidates if p.parent.is_dir()), candidates[0])
    doc = _read_json(path)
    doc, changed = _merge_stdio_server(doc, command=command)
    if changed:
        _write_json(path, doc)
    return {"target": "claude_desktop", "path": str(path), "changed": changed, "ok": True}


def wire_claude_code(command: str) -> dict[str, Any]:
    """User-scope MCP in ``~/.claude.json`` and/or ``claude mcp add``."""
    path = _home() / ".claude.json"
    claude_bin = shutil.which("claude")
    claude_cli: dict[str, Any] | None = None

    if claude_bin:
        # Prefer official writer — keeps Claude Code's schema honest.
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

    doc = _read_json(path)
    doc, changed = _merge_stdio_server(doc, command=command)
    if changed:
        _write_json(path, doc)

    return {
        "target": "claude_code",
        "path": str(path),
        "changed": changed,
        "ok": True,
        "claude_cli": claude_cli,
    }


def wire_all(*, command: str | None = None) -> dict[str, Any]:
    """Wire Cursor + Claude Desktop + Claude Code. Agent runs this — not the human."""
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
    note = (
        "Local STDIO MCP runs on the user's machine with full network. "
        "Call wire ONLY when shell `guru` is unavailable and a local MCP host "
        "needs guru — never every session. Prefer CLI."
    )
    return {
        "ok": True,
        "command": cmd,
        "mode": "stdio",
        "note": note,
        "wired": results,
        "restart_hint": (
            "Restart the MCP host once only if you just wired and tools are missing."
        ),
    }


def wire_status() -> dict[str, Any]:
    cmd = resolve_guru_mcp()
    checks: list[dict[str, Any]] = []
    for label, path, key in (
        ("cursor", _home() / ".cursor" / "mcp.json", "mcpServers"),
        (
            "claude_desktop",
            _home() / ".config" / "Claude" / "claude_desktop_config.json",
            "mcpServers",
        ),
        ("claude_code", _home() / ".claude.json", "mcpServers"),
    ):
        doc = _read_json(path)
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
    return {
        "guru_mcp": cmd,
        "ready": bool(cmd) and any(c["present"] for c in checks),
        "checks": checks,
    }
