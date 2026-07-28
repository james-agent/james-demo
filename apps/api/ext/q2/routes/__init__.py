"""Q2 routes package."""

from fastapi import APIRouter

from ext.q2.routes import accounts, customers, health, provision

router = APIRouter(prefix="/api/v1/q2", tags=["q2"])
router.include_router(health.router)
router.include_router(provision.router)
router.include_router(customers.router)
router.include_router(accounts.router)
