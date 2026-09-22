"""Pure TOML text helpers (no I/O).

Functional core for Codex ``config.toml`` edits. Callers own the filesystem.
"""

from __future__ import annotations

import json
import re
from typing import Any

__all__ = (
    "read_toml_bytes",
    "remove_assignment_in_section",
    "upsert_toml_table",
)


def read_toml_bytes(raw: bytes) -> dict[str, Any]:
    """Parse TOML bytes to a dict; empty/invalid -> {}."""
    import io

    try:
        import tomllib
    except ImportError:  # pragma: no cover - py3.10 without tomli
        return {}
    try:
        data = tomllib.load(io.BytesIO(raw))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _format_value(value: bool | str) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return json.dumps(str(value))


def _format_key(key: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_-]+", key):
        return key
    return json.dumps(str(key))


def remove_assignment_in_section(text: str, section: str, key: str) -> str:
    """Drop ``key = ...`` from ``[section]`` only (for bool->table upgrades)."""
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


def upsert_toml_table(
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
            block_lines.append(f"{_format_key(key)} = {_format_value(value)}")
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
    key_re = re.compile(r'^\s*(?:"([^"]+)"|([A-Za-z0-9_.-]+))\s*=')
    existing_keys: set[str] = set()
    for line in section.splitlines():
        km = key_re.match(line)
        if km:
            existing_keys.add(km.group(1) or km.group(2))

    additions: list[str] = []
    for key, value in entries.items():
        want_line = f"{_format_key(key)} = {_format_value(value)}\n"
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
