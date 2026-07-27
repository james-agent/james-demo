"""Q2 Helix client and gate-check error types."""

from __future__ import annotations


class Q2Error(Exception):
    """Base error for Q2 Helix integration."""

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class Q2ConfigError(Q2Error):
    """Missing or invalid local Q2 configuration (Gate: CONFIG_ERROR)."""


class Q2APIError(Q2Error):
    """Helix API rejected the request or returned a business/auth error."""

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        http_status: int | None = None,
        helix_status: int | None = None,
    ) -> None:
        super().__init__(message, code=code)
        self.http_status = http_status
        self.helix_status = helix_status


class Q2ConnectivityError(Q2Error):
    """Network/timeout failure reaching Helix."""
