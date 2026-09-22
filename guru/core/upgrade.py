"""Installed vs PyPI version -- agents should upgrade before briefing."""

from __future__ import annotations

__all__ = (
    "is_newer",
    "pypi_latest_version",
    "upgrade_status",
)

import json
import re
import urllib.error
import urllib.request
from importlib.metadata import PackageNotFoundError, version
from typing import Any


def _installed_version() -> str:
    try:
        return version("windguru")
    except PackageNotFoundError:
        return "0.0.0"


def _parse_ver(raw: str) -> tuple[int, ...]:
    nums = re.findall(r"\d+", raw.split("+", 1)[0].split("-", 1)[0])
    return tuple(int(x) for x in nums) if nums else (0,)


def is_newer(candidate: str, current: str) -> bool:
    """True only if candidate is strictly newer than current (semver-ish)."""
    return _parse_ver(candidate) > _parse_ver(current)


def pypi_latest_version(*, timeout: float = 4.0) -> str | None:
    """Return latest windguru version on PyPI, or None if unreachable."""
    try:
        req = urllib.request.Request(
            "https://pypi.org/pypi/windguru/json",
            headers={
                "Accept": "application/json",
                "Cache-Control": "no-cache",
                "User-Agent": "windguru-doctor/upgrade-check",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.load(resp)
        ver = data.get("info", {}).get("version")
        return str(ver) if ver else None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None


def upgrade_status() -> dict[str, Any]:
    """Machine-readable upgrade hint for agents."""
    latest = pypi_latest_version()
    current = _installed_version()
    # Only flag upgrade when PyPI is *newer* -- never when CDN lags behind us.
    update = bool(latest and is_newer(latest, current))
    return {
        "installed": current,
        "pypi_latest": latest,
        "update_available": update,
        "upgrade_commands": [
            "pipx upgrade windguru",
            "pipx install --force 'windguru[mcp]'  # pin refresh if CDN lagged",
            "pip install -U 'windguru[mcp]'",
        ],
        "rule": (
            "On every new kite session: if update_available (PyPI newer than "
            "installed), upgrade first, then continue. Prefer pipx. If doctor "
            "shows installed ahead of a stale pypi_latest, do NOT downgrade."
        ),
    }
