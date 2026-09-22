"""Shared CLI catch tuple + app helpers."""

from __future__ import annotations

from guru.search.exceptions import GuruError

try:
    from tenacity import RetryError as _RetryError
except ImportError:  # pragma: no cover
    _RetryError = ()  # type: ignore[misc, assignment]

CATCH = (GuruError, ValueError, OSError, _RetryError)

__all__ = ("CATCH",)
