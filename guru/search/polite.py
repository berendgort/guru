"""Process-wide Windguru politeness: spacing, short TTL cache, ban circuit."""

from __future__ import annotations

__all__ = (
    "CACHE_TTL",
    "MIN_INTERVAL",
    "cache_get",
    "cache_key",
    "cache_set",
    "check_circuit",
    "is_ip_forbidden",
    "reset_polite",
    "trip_circuit",
    "wait_turn",
)

import hashlib
import json
import os
import threading
import time
from typing import Any

from guru.search.exceptions import GuruHTTPError

# Stay well under "scraper" blast rates. Override for tests / emergency.
MIN_INTERVAL = float(os.environ.get("GURU_MIN_INTERVAL", "0.85"))
CACHE_TTL = float(os.environ.get("GURU_CACHE_TTL", "300"))  # seconds
CIRCUIT_TTL = float(os.environ.get("GURU_CIRCUIT_TTL", "3600"))

_lock = threading.Lock()
_last_request_at = 0.0
_circuit_open_until = 0.0
_cache: dict[str, tuple[float, Any]] = {}


def reset_polite() -> None:
    """Clear spacing / cache / circuit (tests)."""
    global _last_request_at, _circuit_open_until, _cache
    with _lock:
        _last_request_at = 0.0
        _circuit_open_until = 0.0
        _cache = {}


def cache_key(base: str, params: dict[str, Any]) -> str:
    payload = json.dumps(
        {"base": base, "params": params}, sort_keys=True, default=str
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def cache_get(key: str) -> Any | None:
    now = time.monotonic()
    with _lock:
        hit = _cache.get(key)
        if hit is None:
            return None
        expires, value = hit
        if expires <= now:
            del _cache[key]
            return None
        return value


def cache_set(key: str, value: Any, *, ttl: float | None = None) -> None:
    life = CACHE_TTL if ttl is None else ttl
    with _lock:
        _cache[key] = (time.monotonic() + life, value)


def check_circuit() -> None:
    with _lock:
        open_until = _circuit_open_until
    if open_until and time.monotonic() < open_until:
        raise GuruHTTPError(
            "Windguru IP Forbidden circuit open -- stop requests; "
            "mail Vaclav if needed. Wait or set GURU_CIRCUIT_TTL=0 to clear "
            "after fix.",
            status_code=403,
        )


def trip_circuit(*, ttl: float | None = None) -> None:
    life = CIRCUIT_TTL if ttl is None else ttl
    global _circuit_open_until
    with _lock:
        _circuit_open_until = time.monotonic() + max(life, 0.0)


def wait_turn(*, min_interval: float | None = None) -> None:
    """Serialize Windguru dials with a minimum gap between requests."""
    gap = MIN_INTERVAL if min_interval is None else min_interval
    global _last_request_at
    with _lock:
        now = time.monotonic()
        delay = (_last_request_at + gap) - now
        if delay > 0:
            time.sleep(delay)
            now = time.monotonic()
        _last_request_at = now


def is_ip_forbidden(status_code: int, body: str) -> bool:
    """Vaclav's anti-scrape Forbidden page (not Claude allowlist 403)."""
    if status_code != 403:
        return False
    text = (body or "").lower()
    if "allowlist" in text or "not allowed" in text or "blocked in this runtime" in text:
        return False
    return (
        "forbidden" in text
        or "do not have permission" in text
        or "provide your ip" in text
    )
