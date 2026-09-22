"""Installed vs PyPI version — agents should upgrade before briefing."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from guru import __version__


def pypi_latest_version(*, timeout: float = 4.0) -> str | None:
    """Return latest windguru version on PyPI, or None if unreachable."""
    try:
        with urllib.request.urlopen(
            "https://pypi.org/pypi/windguru/json", timeout=timeout
        ) as resp:
            data = json.load(resp)
        ver = data.get("info", {}).get("version")
        return str(ver) if ver else None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None


def upgrade_status() -> dict[str, Any]:
    """Machine-readable upgrade hint for agents."""
    latest = pypi_latest_version()
    current = __version__
    update = bool(latest and latest != current)
    return {
        "installed": current,
        "pypi_latest": latest,
        "update_available": update,
        "upgrade_commands": [
            "pipx upgrade windguru",
            "pipx install 'windguru[mcp]'  # if MCP missing",
            "pip install -U 'windguru[mcp]'",
        ],
        "rule": (
            "On every new kite session: if update_available, run an upgrade "
            "command first, then continue. Prefer pipx when the user uses pipx."
        ),
    }
