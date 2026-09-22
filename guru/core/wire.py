"""Auto-wire local STDIO ``guru-mcp`` into agent hosts — no human shell steps."""

from __future__ import annotations

import json
import os
import re
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


# Claude sandbox.allowedDomains patterns (* = subdomain wildcard).
WINDGURU_HOSTS = (
    "www.windguru.cz",
    "windguru.cz",
    "*.windguru.cz",
    "www.windguru.net",
    "windguru.net",
    "*.windguru.net",
)

# Codex / ChatGPT Work network_proxy patterns (** = apex + subdomains).
WINDGURU_CODEX_DOMAINS = (
    "**.windguru.cz",
    "**.windguru.net",
    "www.windguru.cz",
    "www.windguru.net",
    "windguru.cz",
    "windguru.net",
)

# ChatGPT Work / Codex *cloud* environment UI allowlist (no ** syntax there).
WINDGURU_CLOUD_DOMAINS = (
    "windguru.cz",
    "www.windguru.cz",
    "*.windguru.cz",
    "windguru.net",
    "www.windguru.net",
    "*.windguru.net",
)


def unlock_claude_network() -> dict[str, Any]:
    """Open Windguru for Claude Code / Desktop sandboxed shell (allowedDomains).

    This is the real fix for 'Host not in allowlist' when Claude runs guru
    inside its gated bash. Writes ~/.claude/settings.json (user scope).
    """
    path = _home() / ".claude" / "settings.json"
    doc = _read_json(path)
    sandbox = doc.get("sandbox")
    if not isinstance(sandbox, dict):
        sandbox = {}
    network = sandbox.get("network")
    if not isinstance(network, dict):
        network = {}
    domains = network.get("allowedDomains")
    if not isinstance(domains, list):
        domains = []
    changed = False
    for host in WINDGURU_HOSTS:
        if host not in domains:
            domains.append(host)
            changed = True
    network["allowedDomains"] = domains
    sandbox["network"] = network
    doc["sandbox"] = sandbox
    if changed:
        _write_json(path, doc)
    return {
        "target": "claude_network",
        "path": str(path),
        "changed": changed,
        "hosts": list(WINDGURU_HOSTS),
        "ok": True,
        "rider_note": (
            "Wind charts unlocked for Claude on this machine — restart the "
            "Claude chat once, then ask where to kite again."
        ),
    }


def _read_toml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        import tomllib
    except ImportError:  # pragma: no cover — py3.10 without tomli
        return {}
    try:
        with path.open("rb") as fh:
            data = tomllib.load(fh)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _toml_format_value(value: bool | str) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return json.dumps(str(value))


def _toml_format_key(key: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_-]+", key):
        return key
    return json.dumps(str(key))


def _remove_assignment_in_section(text: str, section: str, key: str) -> str:
    """Drop ``key = …`` from ``[section]`` only (for bool→table upgrades)."""
    header_re = re.compile(rf"^\[{re.escape(section)}\]\s*$", re.MULTILINE)
    match = header_re.search(text)
    if not match:
        return text
    start = match.end()
    next_header = re.search(r"^\[", text[start:], re.MULTILINE)
    end = start + next_header.start() if next_header else len(text)
    body = text[start:end]
    body_new, n = re.subn(
        rf"^\s*{re.escape(key)}\s*=\s*.*\n?",
        "",
        body,
        count=1,
        flags=re.MULTILINE,
    )
    if not n:
        return text
    return text[:start] + body_new + text[end:]


def _upsert_toml_table(
    text: str,
    header: str,
    entries: dict[str, bool | str],
) -> tuple[str, bool]:
    """Ensure ``[header]`` exists with key/value rows. Preserve other text."""
    changed = False
    header_re = re.compile(rf"^\[{re.escape(header)}\]\s*$", re.MULTILINE)
    match = header_re.search(text)
    if not match:
        block_lines = [f"[{header}]"]
        for key, value in entries.items():
            block_lines.append(f"{_toml_format_key(key)} = {_toml_format_value(value)}")
        suffix = "\n".join(block_lines) + "\n"
        if text and not text.endswith("\n"):
            text += "\n"
        if text and not text.endswith("\n\n"):
            text += "\n"
        return text + suffix, True

    start = match.end()
    next_header = re.search(r"^\[", text[start:], re.MULTILINE)
    end = start + next_header.start() if next_header else len(text)
    section = text[start:end]
    existing_keys: set[str] = set()
    key_re = re.compile(r'^\s*(?:"([^"]+)"|([A-Za-z0-9_.-]+))\s*=')
    for line in section.splitlines():
        km = key_re.match(line)
        if km:
            existing_keys.add(km.group(1) or km.group(2))

    additions: list[str] = []
    for key, value in entries.items():
        formatted_key = _toml_format_key(key)
        want_line = f"{formatted_key} = {_toml_format_value(value)}\n"
        if key in existing_keys:
            rebuilt: list[str] = []
            updated = False
            for line in section.splitlines(keepends=True):
                stripped = line.rstrip("\n")
                km = key_re.match(stripped)
                line_key = (km.group(1) or km.group(2)) if km else None
                if not updated and line_key == key:
                    if stripped != want_line.rstrip("\n"):
                        changed = True
                    rebuilt.append(want_line)
                    updated = True
                else:
                    rebuilt.append(line)
            section = "".join(rebuilt)
            continue
        additions.append(want_line)
        changed = True

    if additions:
        if section and not section.endswith("\n"):
            section += "\n"
        section = section + "".join(additions)

    return text[:start] + section + text[end:], changed


def unlock_codex_network() -> dict[str, Any]:
    """Open Windguru for local Codex / ChatGPT Work sandboxed shell.

    Writes ``~/.codex/config.toml`` ``features.network_proxy.domains`` allows.
    Skips entirely when ``~/.codex`` is absent (no local Codex/ChatGPT Work).
    Does **not** enable ``network_proxy`` from scratch when it was unset —
    that would lock down every other host. If it was already a boolean
    ``true``/``false``, converts to table form so nested domains are valid TOML.
    """
    codex_home = _home() / ".codex"
    path = codex_home / "config.toml"
    if not codex_home.is_dir() and not path.is_file():
        return {
            "target": "codex_network",
            "skipped": True,
            "reason": "no_codex_home",
            "ok": True,
        }

    raw = path.read_text(encoding="utf-8") if path.is_file() else ""
    data = _read_toml(path)
    features = data.get("features") if isinstance(data.get("features"), dict) else {}
    proxy = features.get("network_proxy")
    proxy_enabled = proxy is True or (
        isinstance(proxy, dict) and proxy.get("enabled") is True
    )

    new_text = raw
    changed = False

    # Bool form cannot nest domains — promote to table, keep prior enabled state.
    if isinstance(proxy, bool):
        new_text = _remove_assignment_in_section(new_text, "features", "network_proxy")
        new_text, c = _upsert_toml_table(
            new_text,
            "features.network_proxy",
            {"enabled": proxy},
        )
        changed = changed or c

    domain_entries: dict[str, bool | str] = {
        host: "allow" for host in WINDGURU_CODEX_DOMAINS
    }
    new_text, c = _upsert_toml_table(
        new_text,
        "features.network_proxy.domains",
        domain_entries,
    )
    changed = changed or c

    # Seed permissions-profile domains when any profile already lists network domains.
    for section_match in re.finditer(
        r"^\[(permissions\.[^\]]+\.network\.domains)\]\s*$",
        new_text,
        re.MULTILINE,
    ):
        header = section_match.group(1)
        new_text, c = _upsert_toml_table(new_text, header, domain_entries)
        changed = changed or c

    if changed:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(new_text, encoding="utf-8")
        try:
            path.chmod(0o600)
        except OSError:
            pass

    return {
        "target": "codex_network",
        "path": str(path),
        "changed": changed,
        "hosts": list(WINDGURU_CODEX_DOMAINS),
        "proxy_was_enabled": proxy_enabled,
        "ok": True,
        "rider_note": (
            "Wind charts unlocked for ChatGPT Work / Codex on this machine — "
            "restart that chat once, then ask where to kite again."
        ),
        "cloud_domains": list(WINDGURU_CLOUD_DOMAINS),
        "cloud_note": (
            "ChatGPT Work / Codex *cloud* chats use the environment Agent "
            "internet allowlist (not this file). Only if still blocked after "
            "local unlock: add cloud_domains there, or continue in Cursor."
        ),
    }


def wire_codex(command: str) -> dict[str, Any]:
    """Ensure ``[mcp_servers.guru]`` in ``~/.codex/config.toml``."""
    codex_home = _home() / ".codex"
    path = codex_home / "config.toml"
    if not codex_home.is_dir() and not path.is_file():
        return {
            "target": "codex",
            "skipped": True,
            "reason": "no_codex_home",
            "ok": True,
        }
    raw = path.read_text(encoding="utf-8") if path.is_file() else ""
    new_text, changed = _upsert_toml_table(
        raw,
        "mcp_servers.guru",
        {"command": command},
    )
    if changed:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(new_text, encoding="utf-8")
        try:
            path.chmod(0o600)
        except OSError:
            pass
    return {
        "target": "codex",
        "path": str(path),
        "changed": changed,
        "ok": True,
    }


def _claude_wind_open() -> bool:
    settings = _read_json(_home() / ".claude" / "settings.json")
    domains = (
        ((settings.get("sandbox") or {}).get("network") or {}).get("allowedDomains")
        if isinstance(settings, dict)
        else None
    )
    return isinstance(domains, list) and "www.windguru.cz" in domains


def _codex_wind_open() -> bool:
    path = _home() / ".codex" / "config.toml"
    if not path.is_file():
        return False
    data = _read_toml(path)
    features = data.get("features") if isinstance(data.get("features"), dict) else {}
    proxy = features.get("network_proxy")
    if not isinstance(proxy, dict):
        return False
    domains = proxy.get("domains")
    if not isinstance(domains, dict):
        return False
    return any(
        domains.get(h) == "allow"
        for h in ("**.windguru.cz", "www.windguru.cz", "windguru.cz")
    )


def unlock_wind_charts(
    *,
    command: str | None = None,
    force: bool = False,
    wire: bool = True,
) -> dict[str, Any]:
    """Open Windguru for Claude + Codex/ChatGPT Work — only when blocked.

    Default: probe first. If Windguru is already reachable, skip all writes
    (``skipped=true``). Pass ``force=True`` to write allowlists anyway.
    """
    from guru.core.path import probe_windguru

    probe = probe_windguru()
    reachable = probe.get("reachable") is True
    if reachable and not force:
        return {
            "ok": True,
            "skipped": True,
            "reason": "already_reachable",
            "probe": probe,
            "say_to_rider": None,
            "agent_note": (
                "Wind already reachable — unlock not needed. Do not mention "
                "allowlists. Proceed with weekend/best."
            ),
        }

    claude_net = unlock_claude_network()
    codex_net = unlock_codex_network()

    wired: dict[str, Any] | None = None
    if wire:
        wired = wire_all(command=command)
        cmd = (wired or {}).get("command") or command or resolve_guru_mcp()
        if cmd:
            codex_wire = wire_codex(cmd)
            if isinstance(wired, dict):
                wired = {**wired, "codex": codex_wire}

    ok = bool(claude_net.get("ok")) and bool(codex_net.get("ok"))
    if wired is not None:
        ok = ok and bool(wired.get("ok", True))

    from guru.core.human_fix import human_fix_payload, pick_human_fix

    restart = pick_human_fix(after_unlock=True)
    return {
        "ok": ok,
        "skipped": False,
        "probe": probe,
        "claude_network": claude_net,
        "codex_network": codex_net,
        "network": claude_net,  # back-compat for older agents
        "wired": wired,
        "say_to_rider": (restart or {}).get("say_to_rider")
        or (
            "Wind's unlocked on your laptop. Start a new chat, then ask: "
            "where can I kite?"
        ),
        "human_fix": restart,
        "human_fix_catalog": human_fix_payload(),
        "agent_note": (
            "Unlock only when network.reachable was false (or --force). "
            "You automated the laptop writes — paste say_to_rider "
            "(restart new chat). If still blocked after restart, paste "
            "exactly one recipe from human_fix_catalog.recipes for the "
            "host (chatgpt_work_network / codex_cloud_environment / "
            "claude_network_settings / fallback_cursor). Never invent steps; "
            "never ask for pipx or shell."
        ),
    }


def unlock_for_claude(*, command: str | None = None, force: bool = False) -> dict[str, Any]:
    """Back-compat alias — same as ``unlock_wind_charts``."""
    return unlock_wind_charts(command=command, force=force)


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
    # Codex MCP (toml)
    codex_path = _home() / ".codex" / "config.toml"
    codex_doc = _read_toml(codex_path)
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
    claude_open = _claude_wind_open()
    codex_open = _codex_wind_open()
    return {
        "guru_mcp": cmd,
        "ready": bool(cmd) and any(c["present"] for c in checks),
        "windguru_unlocked": claude_open or codex_open,
        "claude_unlocked": claude_open,
        "codex_unlocked": codex_open,
        "checks": checks,
    }
