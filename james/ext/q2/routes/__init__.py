"""Q2 connection and domain routes package."""

from james.ext.q2.routes.accounts import router as accounts_router
from james.ext.q2.routes.connection import router as connection_router
from james.ext.q2.routes.customers import router as customers_router

__all__ = ["accounts_router", "connection_router", "customers_router"]
