"""Shared error classification for CLI and MCP."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from guru.core.exceptions import (
    GuruAmbiguousError,
    GuruError,
    GuruHTTPError,
    GuruNotFoundError,
    GuruParseError,
)

__all__ = (
    "ErrorClassification",
    "GuruAmbiguousError",
    "GuruError",
    "GuruHTTPError",
    "GuruNotFoundError",
    "GuruParseError",
    "classify_error",
)

_RETRYABLE_HTTP = {429}


@dataclass(frozen=True)
class ErrorClassification:
    error_type: str
    retryable: bool
    http_status: int | None = None

    def as_fields(self) -> dict[str, Any]:
        fields: dict[str, Any] = {
            "error_type": self.error_type,
            "retryable": self.retryable,
        }
        if self.http_status is not None:
            fields["http_status"] = self.http_status
        return fields


def classify_error(exc: BaseException) -> ErrorClassification:
    """Map an exception to a stable ``error_type`` + ``retryable`` pair."""
    cause = getattr(exc, "last_attempt", None)
    if cause is not None:
        try:
            inner = cause.exception()
            if inner is not None:
                return classify_error(inner)
        except Exception:  # noqa: BLE001
            pass
    if isinstance(exc, GuruAmbiguousError):
        return ErrorClassification("ambiguous", retryable=False)
    if isinstance(exc, GuruNotFoundError):
        return ErrorClassification("not_found", retryable=False)
    if isinstance(exc, GuruParseError):
        return ErrorClassification("parse_error", retryable=False)
    if isinstance(exc, GuruHTTPError):
        status = getattr(exc, "status_code", None)
        msg = str(exc).lower()
        if (
            "ip ban" in msg
            or "circuit open" in msg
            or "anti-scrape" in msg
            or ("forbidden" in msg and status == 403)
        ):
            return ErrorClassification(
                "rate_limited", retryable=False, http_status=status
            )
        if status == 403 or "allowlist" in msg or "blocked in this runtime" in msg:
            return ErrorClassification(
                "connection_error", retryable=False, http_status=status
            )
        retryable = status is not None and (status in _RETRYABLE_HTTP or status >= 500)
        return ErrorClassification("http_error", retryable=retryable, http_status=status)
    if isinstance(exc, TimeoutError):
        return ErrorClassification("timeout", retryable=True)
    if isinstance(exc, ConnectionError | OSError):
        return ErrorClassification("connection_error", retryable=True)
    if isinstance(exc, ValueError):
        return ErrorClassification("validation_error", retryable=False)
    if isinstance(exc, GuruError):
        return ErrorClassification("search_error", retryable=False)
    msg = str(exc).lower()
    if "timeout" in msg:
        return ErrorClassification("timeout", retryable=True)
    if "429" in msg or "rate" in msg:
        return ErrorClassification("rate_limited", retryable=True, http_status=429)
    if "allowlist" in msg or "retryerror" in type(exc).__name__.lower():
        return ErrorClassification("connection_error", retryable=False)
    return ErrorClassification("unexpected_error", retryable=False)
