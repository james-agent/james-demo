"""Authenticated Q2 Helix HTTP client (owned by q2-authentication)."""

from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

import httpx

from ext.q2.config import Q2Config, load_q2_config
from ext.q2.errors import Q2ConfigError, Q2Error, classify_http_error


class HelixClient:
    """HTTP Basic Auth client for Q2 Helix relative paths."""

    def __init__(self, config: Q2Config | None = None, *, transport: httpx.BaseTransport | None = None) -> None:
        self.config = config or load_q2_config()
        self._client = httpx.Client(
            base_url=self.config.api_url.rstrip("/") + "/",
            auth=(self.config.api_key, self.config.api_secret),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=self.config.timeout_seconds,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> HelixClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def ensure_configured(self) -> None:
        if self.config.mock_mode:
            return
        missing = self.config.missing_keys
        if missing:
            raise Q2ConfigError(
                "Missing required Q2 Helix environment variables.",
                missing_keys=missing,
            )

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        self.ensure_configured()
        relative = path.lstrip("/")
        if self.config.mock_mode:
            return {"status": 0, "message": "Success", "data": {"mock": True, "path": relative}}

        response = self._client.request(method.upper(), relative, json=payload or {})
        body_text = response.text
        if response.status_code >= 400:
            raise classify_http_error(response.status_code, body_text)
        try:
            data = response.json()
        except ValueError as exc:
            raise Q2Error(
                "Helix returned non-JSON response.",
                code="API_BUSINESS_ERROR",
                http_status=response.status_code,
                details={"body": body_text[:300]},
            ) from exc
        if isinstance(data, dict) and data.get("status", 0) not in (0, "0", None):
            raise Q2Error(
                str(data.get("message") or "Helix business error"),
                code="API_BUSINESS_ERROR",
                http_status=response.status_code,
                details={"helix_status": data.get("status")},
            )
        return data if isinstance(data, dict) else {"data": data}

    def get(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.request("GET", path, payload)

    def post(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.request("POST", path, payload)

    def test_connectivity(self) -> dict[str, Any]:
        """Official Test Connectivity: authenticated GET to Helix base URL."""
        self.ensure_configured()
        if self.config.mock_mode:
            return {
                "ok": True,
                "mode": "mock",
                "environment": self.config.environment,
                "message": "Mock Helix connectivity OK",
            }
        # Prefer root welcome JSON; fall back to program/get.
        try:
            response = self._client.get("")
            if response.status_code < 400:
                return {
                    "ok": True,
                    "environment": self.config.environment,
                    "http_status": response.status_code,
                    "message": "Helix base connectivity OK",
                }
        except httpx.HTTPError as exc:
            raise Q2Error(
                f"Helix connectivity failed: {exc.__class__.__name__}",
                code="CONNECTIVITY_ERROR",
            ) from exc
        program = self.post("program/get", {"programId": self.config.program_id})
        return {
            "ok": True,
            "environment": self.config.environment,
            "message": "Helix program/get OK",
            "program": program.get("data") if isinstance(program, dict) else program,
        }

    def absolute_url(self, path: str) -> str:
        return urljoin(self.config.api_url.rstrip("/") + "/", path.lstrip("/"))
