"""CRM API application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from crm_api.config import get_settings
from crm_api.db import get_session_factory, init_db
from crm_api.routes import crm_customers, health
from crm_api.services.customer_registry import import_mock_customers
from ext.q2.routes import customers as q2_customers
from ext.q2.routes import sync as q2_sync

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    session = get_session_factory()()
    try:
        import_mock_customers(session)
    finally:
        session.close()
    yield


app = FastAPI(
    title="CRM API",
    description="Customer registration CRM with Q2 Helix integration",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(crm_customers.router)
app.include_router(q2_customers.router)
app.include_router(q2_sync.router)
