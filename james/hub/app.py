"""Minimal FastAPI hub for Q2 Helix connection, customer, and account endpoints."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from james.config import get_app_config
from james.ext.q2.routes.accounts import router as q2_accounts_router
from james.ext.q2.routes.connection import router as q2_connection_router
from james.ext.q2.routes.customers import router as q2_customers_router

settings = get_app_config()

app = FastAPI(
    title="James Demo API",
    description="Q2 Helix hub (connection, customers, accounts)",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(q2_connection_router)
app.include_router(q2_customers_router)
app.include_router(q2_accounts_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "james-hub"}
