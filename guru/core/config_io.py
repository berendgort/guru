"""Config path helpers (small I/O shell). Shared by wire + unlock."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from guru.core.toml_edit import read_toml_bytes

__all__ = (
    "home",
    "read_json",
    "write_json",
    "read_toml",
    "write_text_secure",
)


def home() -> Path:
    return Path.home()


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass


def read_toml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return read_toml_bytes(path.read_bytes())
    except OSError:
        return {}


def write_text_secure(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
