"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Liveness probe — confirms the CRM API process is running."""
    return {"status": "ok", "service": "crm-api"}
