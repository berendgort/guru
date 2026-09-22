"""CLI emit / fail helpers (stdout JSON + Rich)."""

from __future__ import annotations

import json
import sys
from typing import Any

import typer

from guru.cli.console import console
from guru.core.envelope import error_payload, success_payload
from guru.core.errors import classify_error


def emit_json(data: Any) -> None:
    """Write JSON to stdout (success or pre-built envelope)."""
    sys.stdout.write(json.dumps(data, default=str) + "\n")


def print_ok(data: Any) -> None:
    """Emit a success envelope."""
    emit_json(success_payload(data))


def fail(exc: BaseException, *, as_json: bool) -> None:
    """Print error (JSON or Rich) and exit with a stable code."""
    # Unwrap tenacity RetryError so we don't dump a stack to humans/agents.
    inner = _unwrap(exc)
    classified = classify_error(inner)
    code = 2 if classified.retryable else 1
    if as_json:
        emit_json(error_payload(inner))
        raise typer.Exit(code) from exc
    console.print(f"[red]{inner}[/red]")
    raise typer.Exit(code) from exc


def _unwrap(exc: BaseException) -> BaseException:
    attempt = getattr(exc, "last_attempt", None)
    if attempt is not None:
        try:
            nested = attempt.exception()
            if nested is not None:
                return nested
        except Exception:  # noqa: BLE001
            pass
    return exc
