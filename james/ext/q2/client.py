"""HTTP client for Q2 Helix API (Basic Auth). Owned by q2-authentication."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from james.ext.q2.config import Q2Config, get_q2_config
from james.ext.q2.errors import Q2APIError, Q2ConnectivityError

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
_POOL_LIMITS = httpx.Limits(max_connections=20, max_keepalive_connections=10)


class HelixClient:
    """Server-side Helix client. Never expose credentials to browsers."""

    def __init__(
        self,
        config: Q2Config | None = None,
        *,
        client: httpx.Client | None = None,
    ) -> None:
        self._config = config or get_q2_config()
        self._owns_client = client is None
        self._client = client or httpx.Client(
            timeout=_DEFAULT_TIMEOUT,
            limits=_POOL_LIMITS,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> HelixClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _url(self, path: str) -> str:
        base = self._config.helix_base_url.rstrip("/")
        relative = path.lstrip("/")
        return f"{base}/{relative}"

    def _auth(self) -> httpx.BasicAuth:
        return httpx.BasicAuth(
            self._config.q2_helix_api_key.strip(),
            self._config.q2_helix_api_secret.strip(),
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Perform an authenticated Helix request. Relative ``path`` only."""
        self._config.require_helix()
        url = self._url(path)
        try:
            response = self._client.request(
                method.upper(),
                url,
                auth=self._auth(),
                json=json_body if json_body is not None else {},
            )
        except httpx.TimeoutException as exc:
            raise Q2ConnectivityError(
                f"Helix request timed out ({method.upper()} {path})",
                code="TIMEOUT",
            ) from exc
        except httpx.TransportError as exc:
            raise Q2ConnectivityError(
                f"Helix transport error ({method.upper()} {path}): {exc!s}"[:300],
                code="TRANSPORT",
            ) from exc

        return self._parse_response(response, path=path)

    def _parse_response(self, response: httpx.Response, *, path: str) -> dict[str, Any]:
        status = response.status_code
        if status == 401:
            raise Q2APIError(
                "Helix authentication failed (401). Verify Q2_HELIX_API_KEY / Q2_HELIX_API_SECRET.",
                code="UNAUTHORIZED",
                http_status=401,
            )
        if status == 403:
            raise Q2APIError(
                "Helix forbidden (403). Confirm the calling IP is whitelisted for this environment.",
                code="FORBIDDEN",
                http_status=403,
            )
        if status == 404:
            raise Q2APIError(
                f"Helix resource not found (404) for path '{path}'.",
                code="NOT_FOUND",
                http_status=404,
            )
        if status == 429:
            raise Q2APIError(
                "Helix rate limit exceeded (429).",
                code="RATE_LIMITED",
                http_status=429,
            )
        if status >= 500:
            raise Q2APIError(
                f"Helix server error ({status}).",
                code="SERVER_ERROR",
                http_status=status,
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise Q2APIError(
                f"Helix returned non-JSON response (HTTP {status}).",
                code="INVALID_JSON",
                http_status=status,
            ) from exc

        if not isinstance(payload, dict):
            raise Q2APIError(
                "Helix returned an unexpected JSON payload.",
                code="INVALID_PAYLOAD",
                http_status=status,
            )

        helix_status = payload.get("status")
        if helix_status not in (None, 0, "0"):
            message = str(payload.get("message") or "Helix business error")
            raise Q2APIError(
                message,
                code="HELIX_BUSINESS",
                http_status=status,
                helix_status=int(helix_status) if str(helix_status).lstrip("-").isdigit() else None,
            )

        if status >= 400:
            raise Q2APIError(
                f"Helix HTTP error ({status}).",
                code="HTTP_ERROR",
                http_status=status,
            )

        return payload

    def test_connectivity(self) -> dict[str, Any]:
        """Hit Helix root (welcome) then fall back to program/get."""
        self._config.require_helix()
        url = self._config.helix_base_url.rstrip("/") + "/"
        try:
            response = self._client.get(url, auth=self._auth())
        except httpx.TimeoutException as exc:
            raise Q2ConnectivityError("Helix connectivity probe timed out", code="TIMEOUT") from exc
        except httpx.TransportError as exc:
            raise Q2ConnectivityError(
                f"Helix connectivity probe failed: {exc!s}"[:300],
                code="TRANSPORT",
            ) from exc

        if response.status_code in {200, 401, 403}:
            if response.status_code == 200:
                try:
                    body = response.json()
                except ValueError:
                    body = {"raw": (response.text or "")[:200]}
                return {
                    "probe": "root",
                    "http_status": 200,
                    "welcome": body,
                }
            # Re-raise through shared parser for consistent messaging
            self._parse_response(response, path="/")

        return self.get_program()

    def get_program(self, program_id: str | None = None) -> dict[str, Any]:
        """POST program/get — discover program configuration and products."""
        body: dict[str, Any] = {}
        pid = (program_id or self._config.q2_helix_program_id or "").strip()
        if pid:
            body["programId"] = pid
        payload = self.request("POST", "program/get", json_body=body)
        return {
            "probe": "program/get",
            "http_status": 200,
            "program": payload.get("data") if isinstance(payload.get("data"), dict) else payload,
            "raw_status": payload.get("status", 0),
            "message": payload.get("message"),
        }
