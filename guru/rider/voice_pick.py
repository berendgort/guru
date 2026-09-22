"""Deterministic joke / tagline / call-label picks (pure)."""

from __future__ import annotations

import zlib
from collections.abc import Sequence

from guru.rider.voice_bank import CALL, JOKES, TAGLINES

__all__ = ("call_label", "joke", "tagline")


def _pick(items: Sequence[str], key: str) -> str:
    if not items:
        return ""
    return items[zlib.adler32(key.encode("utf-8")) % len(items)]


def tagline(*, seed: str = "banner") -> str:
    return _pick(TAGLINES, seed)


def joke(*, about: str = "general", seed: str | None = None) -> str:
    pool = JOKES.get(about) or JOKES["general"]
    return _pick(pool, seed or about)


def call_label(verdict: str) -> str:
    return CALL.get(verdict, verdict.upper())
