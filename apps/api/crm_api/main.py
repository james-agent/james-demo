"""CRM API application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from crm_api.config import get_settings
from crm_api.routes import crm_customers, health
from ext.q2.db import Base, get_engine
from ext.q2.routes import router as q2_router
import ext.q2.models  # noqa: F401 — register ORM metadata

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Ensure Q2 mapping tables exist (Alembic remains source of truth for prod upgrades).
    Base.metadata.create_all(bind=get_engine())
    yield


app = FastAPI(
    title="CRM API",
    description="Customer registration CRM with Q2 Helix provisioning",
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
app.include_router(q2_router)
