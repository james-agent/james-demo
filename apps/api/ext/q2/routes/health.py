"""Q2 Helix health / connectivity endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from ext.q2.client import HelixClient
from ext.q2.config import load_q2_config
from ext.q2.errors import Q2Error
from ext.q2.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def q2_health() -> HealthResponse:
    config = load_q2_config()
    missing = config.missing_keys
    if missing and not config.mock_mode:
        return HealthResponse(
            ok=False,
            environment=config.environment,
            configured=False,
            mock_mode=False,
            missing_keys=missing,
            error="Missing required Q2 Helix environment variables.",
            code="CONFIG_ERROR",
        )

    client = HelixClient(config)
    try:
        connectivity = client.test_connectivity()
        return HealthResponse(
            ok=True,
            environment=config.environment,
            configured=True,
            mock_mode=config.mock_mode,
            missing_keys=[],
            connectivity=connectivity,
        )
    except Q2Error as exc:
        return HealthResponse(
            ok=False,
            environment=config.environment,
            configured=True,
            mock_mode=config.mock_mode,
            missing_keys=[],
            error=exc.message,
            code=exc.code,
        )
    finally:
        client.close()
