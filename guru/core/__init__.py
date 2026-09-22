"""Shared core utilities (CLI + MCP)."""

from guru.core.envelope import (
    API_VERSION,
    ERROR_SCHEMA,
    dump_model,
    error_payload,
    success_payload,
)
from guru.core.errors import ErrorClassification, classify_error
from guru.core.instruct import instruct_payload

__all__ = [
    "API_VERSION",
    "ERROR_SCHEMA",
    "ErrorClassification",
    "classify_error",
    "dump_model",
    "error_payload",
    "instruct_payload",
    "success_payload",
]
