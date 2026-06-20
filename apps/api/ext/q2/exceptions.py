"""Q2 Helix API error types."""

from __future__ import annotations


class Q2ApiError(Exception):
    """Base error for Q2 Helix API failures."""

    def __init__(self, message: str, *, status_code: int | None = None, code: str | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code


class Q2DuplicateTagError(Q2ApiError):
    """Raised when a customer tag already exists in Q2 (HTTP 409)."""
