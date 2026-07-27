"""Q2 Helix connection status and connectivity test endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from james.ext.q2.client import HelixClient
from james.ext.q2.config import get_q2_config, reset_q2_config
from james.ext.q2.errors import Q2APIError, Q2ConfigError, Q2ConnectivityError

router = APIRouter(prefix="/api/v1/q2/connection", tags=["q2-connection"])


class ConnectionStatusResponse(BaseModel):
    environment: str
    helix_base_url: str
    helix_configured: bool
    helix_api_key_set: bool
    helix_api_secret_set: bool
    helix_program_id_set: bool
    caliper_configured: bool
    amqp_configured: bool
    missing_helix_vars: list[str] = Field(default_factory=list)


class ConnectionTestResponse(BaseModel):
    result: str
    environment: str
    helix_base_url: str
    detail: dict[str, Any] = Field(default_factory=dict)
    products: list[Any] = Field(default_factory=list)
    program_id: str | None = None


def _product_summary(program: dict[str, Any] | None) -> tuple[str | None, list[Any]]:
    if not program:
        return None, []
    program_id = program.get("programId") or program.get("program_id")
    products = program.get("products") or []
    if not isinstance(products, list):
        products = []
    # Never return nested secrets / public keys in full — trim to identifiers
    slim: list[Any] = []
    for item in products:
        if isinstance(item, dict):
            slim.append(
                {
                    "productId": item.get("productId") or item.get("product_id"),
                    "name": item.get("name") or item.get("productName"),
                    "type": item.get("type") or item.get("productType"),
                }
            )
        else:
            slim.append(item)
    return (str(program_id) if program_id is not None else None), slim


@router.get("/status", response_model=ConnectionStatusResponse)
def connection_status() -> ConnectionStatusResponse:
    """Return configuration flags without exposing secrets."""
    reset_q2_config()
    cfg = get_q2_config()
    return ConnectionStatusResponse(
        environment=cfg.q2_environment,
        helix_base_url=cfg.helix_base_url,
        helix_configured=cfg.helix_configured,
        helix_api_key_set=bool(cfg.q2_helix_api_key.strip()),
        helix_api_secret_set=bool(cfg.q2_helix_api_secret.strip()),
        helix_program_id_set=bool(cfg.q2_helix_program_id.strip()),
        caliper_configured=cfg.caliper_configured,
        amqp_configured=cfg.amqp_configured,
        missing_helix_vars=cfg.missing_helix_vars(),
    )


@router.post("/test", response_model=ConnectionTestResponse)
def connection_test() -> ConnectionTestResponse:
    """Test Helix Basic Auth connectivity and discover program products."""
    reset_q2_config()
    cfg = get_q2_config()
    try:
        with HelixClient(cfg) as client:
            try:
                probe = client.test_connectivity()
            except Q2APIError:
                # Root probe may be unavailable; program/get is the authoritative check
                probe = client.get_program()
            else:
                if probe.get("probe") == "root":
                    try:
                        program_probe = client.get_program()
                        probe = {**probe, "program_probe": program_probe}
                    except Q2APIError as exc:
                        probe = {**probe, "program_probe_error": exc.message}

        program_data: dict[str, Any] | None = None
        if isinstance(probe.get("program"), dict):
            program_data = probe["program"]
        elif isinstance(probe.get("program_probe"), dict):
            nested = probe["program_probe"].get("program")
            if isinstance(nested, dict):
                program_data = nested

        program_id, products = _product_summary(program_data)
        return ConnectionTestResponse(
            result="PASS",
            environment=cfg.q2_environment,
            helix_base_url=cfg.helix_base_url,
            detail={"probe": probe.get("probe"), "http_status": probe.get("http_status")},
            products=products,
            program_id=program_id or (cfg.q2_helix_program_id or None),
        )
    except Q2ConfigError as exc:
        raise HTTPException(
            status_code=400,
            detail={"result": "CONFIG_ERROR", "message": exc.message, "code": exc.code},
        ) from exc
    except Q2ConnectivityError as exc:
        raise HTTPException(
            status_code=503,
            detail={"result": "API_BUSINESS_ERROR", "message": exc.message, "code": exc.code},
        ) from exc
    except Q2APIError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "result": "API_BUSINESS_ERROR",
                "message": exc.message,
                "code": exc.code,
                "http_status": exc.http_status,
            },
        ) from exc
