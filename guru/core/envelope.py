"""Shared JSON envelope for CLI and MCP (agent contract)."""

from __future__ import annotations

from typing import Any

from guru.core.errors import classify_error
from guru.search.exceptions import GuruAmbiguousError

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
    classified = classify_error(exc)
    payload: dict[str, Any] = {
        "ok": False,
        "api_version": API_VERSION,
        "error": str(exc),
        **classified.as_fields(),
    }
    if isinstance(exc, GuruAmbiguousError):
        payload["candidates"] = [c.model_dump(mode="json") for c in exc.candidates]
    return payload


def dump_model(model: Any) -> Any:
    """Pydantic model → JSON-ready dict."""
    return model.model_dump(mode="json")
