"""Shared JSON envelope for CLI and MCP (agent contract)."""

from __future__ import annotations

__all__ = (
    "API_VERSION",
    "ERROR_SCHEMA",
    "dump_model",
    "error_payload",
    "success_payload",
)

from typing import Any

from guru.core.errors import classify_error
from guru.core.exceptions import GuruAmbiguousError

API_VERSION = 1

ERROR_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "ok": {"const": False},
        "api_version": {"type": "integer"},
        "error": {"type": "string"},
        "error_type": {"type": "string"},
        "retryable": {"type": "boolean"},
        "http_status": {"type": "integer"},
        "candidates": {"type": "array"},
    },
}


def success_payload(data: Any) -> dict[str, Any]:
    return {"ok": True, "api_version": API_VERSION, "data": data}


def error_payload(exc: BaseException) -> dict[str, Any]:
    # Prefer the underlying HTTP/allowlist error over tenacity RetryError text.
    attempt = getattr(exc, "last_attempt", None)
    if attempt is not None:
        try:
            nested = attempt.exception()
            if nested is not None:
                exc = nested
        except Exception:  # noqa: BLE001
            pass
    classified = classify_error(exc)
    payload: dict[str, Any] = {
        "ok": False,
        "api_version": API_VERSION,
        "error": str(exc),
        **classified.as_fields(),
    }
    if isinstance(exc, GuruAmbiguousError):
        payload["candidates"] = [c.model_dump(mode="json") for c in exc.candidates]
    from guru.core.gated import gated_fields, is_gated

    if is_gated(exc):
        msg = str(exc).lower()
        done = (
            "do not run unlock again" in msg
            or "unlock again" in msg
            or "allowlist already written" in msg
        )
        payload.update(gated_fields(unlock_already_done=True if done else None))
    return payload


def dump_model(model: Any) -> Any:
    """Pydantic model → JSON-ready dict."""
    return model.model_dump(mode="json")
