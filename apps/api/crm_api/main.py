"""CRM API application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from crm_api.config import get_settings
from crm_api.db import init_db
from crm_api.ext.q2.routes import accounts as q2_accounts
from crm_api.ext.q2.routes import customers as q2_customers
from crm_api.ext.q2.routes import sync as q2_sync
from crm_api.routes import crm_customers, health, local_customers

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="CRM API",
    description="Customer registration CRM with Q2 Helix customer/account integration",
    version="0.3.0",
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
app.include_router(local_customers.router)
app.include_router(q2_customers.router)
app.include_router(q2_accounts.router)
app.include_router(q2_sync.router)
