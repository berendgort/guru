"""Unlock Windguru hosts for Claude + Codex/ChatGPT Work sandboxes.

Imperative shell: probe, write allowlists, optional MCP wire.
Only runs writes when charts are gated (or force=True).
"""

from __future__ import annotations

import re
from typing import Any

from guru.core.config_io import home, read_json, read_toml, write_json, write_text_secure
from guru.core.hosts import WINDGURU_CLOUD_DOMAINS, WINDGURU_CODEX_DOMAINS, WINDGURU_HOSTS
from guru.core.toml_edit import remove_assignment_in_section, upsert_toml_table

__all__ = (
    "unlock_claude_network",
    "unlock_codex_network",
    "unlock_wind_charts",
    "unlock_for_claude",
    "claude_wind_open",
    "codex_wind_open",
)


def unlock_claude_network() -> dict[str, Any]:
    """Open Windguru for Claude Code / Desktop (sandbox.allowedDomains)."""
    path = home() / ".claude" / "settings.json"
    doc = read_json(path)
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
        write_json(path, doc)
    return {
        "target": "claude_network",
        "path": str(path),
        "changed": changed,
        "hosts": list(WINDGURU_HOSTS),
        "ok": True,
        "rider_note": (
            "Wind charts unlocked for Claude on this machine -- restart the "
            "Claude chat once, then ask where to kite again."
        ),
    }


def unlock_codex_network() -> dict[str, Any]:
    """Open Windguru for local Codex / ChatGPT Work (config.toml domains).

    Skips when ``~/.codex`` is absent. Does not enable network_proxy from
    scratch (that would lock down every other host). Bool proxy form is
    promoted to a table so nested domains are valid TOML.
    """
    codex_home = home() / ".codex"
    path = codex_home / "config.toml"
    if not codex_home.is_dir() and not path.is_file():
        return {
            "target": "codex_network",
            "skipped": True,
            "reason": "no_codex_home",
            "ok": True,
        }

    raw = path.read_text(encoding="utf-8") if path.is_file() else ""
    data = read_toml(path)
    features = data.get("features") if isinstance(data.get("features"), dict) else {}
    proxy = features.get("network_proxy")
    proxy_enabled = proxy is True or (
        isinstance(proxy, dict) and proxy.get("enabled") is True
    )

    new_text = raw
    changed = False

    if isinstance(proxy, bool):
        new_text = remove_assignment_in_section(new_text, "features", "network_proxy")
        new_text, c = upsert_toml_table(
            new_text,
            "features.network_proxy",
            {"enabled": proxy},
        )
        changed = changed or c

    domain_entries: dict[str, bool | str] = {
        host: "allow" for host in WINDGURU_CODEX_DOMAINS
    }
    new_text, c = upsert_toml_table(
        new_text,
        "features.network_proxy.domains",
        domain_entries,
    )
    changed = changed or c

    for section_match in re.finditer(
        r"^\[(permissions\.[^\]]+\.network\.domains)\]\s*$",
        new_text,
        re.MULTILINE,
    ):
        new_text, c = upsert_toml_table(new_text, section_match.group(1), domain_entries)
        changed = changed or c

    if changed:
        write_text_secure(path, new_text)

    return {
        "target": "codex_network",
        "path": str(path),
        "changed": changed,
        "hosts": list(WINDGURU_CODEX_DOMAINS),
        "proxy_was_enabled": proxy_enabled,
        "ok": True,
        "rider_note": (
            "Wind charts unlocked for ChatGPT Work / Codex on this machine -- "
            "restart that chat once, then ask where to kite again."
        ),
        "cloud_domains": list(WINDGURU_CLOUD_DOMAINS),
        "cloud_note": (
            "ChatGPT Work / Codex *cloud* chats use the environment Agent "
            "internet allowlist (not this file). Only if still blocked after "
            "local unlock: add cloud_domains there, or continue in Cursor."
        ),
    }


def claude_wind_open() -> bool:
    settings = read_json(home() / ".claude" / "settings.json")
    domains = (
        ((settings.get("sandbox") or {}).get("network") or {}).get("allowedDomains")
        if isinstance(settings, dict)
        else None
    )
    return isinstance(domains, list) and "www.windguru.cz" in domains


def codex_wind_open() -> bool:
    path = home() / ".codex" / "config.toml"
    if not path.is_file():
        return False
    data = read_toml(path)
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
    """Open Windguru for Claude + Codex -- only when blocked (unless force)."""
    from guru.core.human_fix import pick_human_fix
    from guru.core.path import probe_windguru
    from guru.core.wire import resolve_guru_mcp, wire_all, wire_codex

    probe = probe_windguru()
    if probe.get("reachable") is True and not force:
        return {
            "ok": True,
            "skipped": True,
            "reason": "already_reachable",
            "probe": probe,
            "say_to_rider": None,
            "agent_note": (
                "Wind already reachable -- unlock not needed. Do not mention "
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

    restart = pick_human_fix(after_unlock=True)
    return {
        "ok": ok,
        "skipped": False,
        "probe": probe,
        "claude_network": claude_net,
        "codex_network": codex_net,
        "network": claude_net,
        "wired": wired,
        "say_to_rider": (restart or {}).get("say_to_rider")
        or (
            "Wind's unlocked on your laptop. Start a new chat, then ask: "
            "where can I kite?"
        ),
        "human_fix": restart,
        "agent_note": (
            "Unlock only when network.reachable was false (or --force). "
            "Paste say_to_rider (restart new chat). If still blocked, paste "
            "exactly one instruct.human_fix.recipes[*].say_to_rider for the "
            "host. Never invent steps; never ask for pipx or shell."
        ),
    }


def unlock_for_claude(*, command: str | None = None, force: bool = False) -> dict[str, Any]:
    """Back-compat alias for ``unlock_wind_charts``."""
    return unlock_wind_charts(command=command, force=force)
