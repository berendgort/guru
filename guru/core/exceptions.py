"""Shared guru error types (foundation -- importable by core + search)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from guru.models.forecast import Spot

__all__ = (
    "GuruAmbiguousError",
    "GuruError",
    "GuruHTTPError",
    "GuruNotFoundError",
    "GuruParseError",
)


class GuruError(Exception):
    """Base."""


class GuruHTTPError(GuruError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class GuruParseError(GuruError):
    pass


class GuruNotFoundError(GuruError):
    pass


class GuruAmbiguousError(GuruError):
    """Multiple spots matched a name; caller must pick an id."""

    def __init__(self, message: str, *, candidates: list[Spot]) -> None:
        super().__init__(message)
        self.candidates = candidates
