"""CRM API application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from crm_api.config import get_settings
from crm_api.ext.q2.routes import accounts as q2_accounts
from crm_api.ext.q2.routes import customers as q2_customers
from crm_api.routes import crm_customers, health

settings = get_settings()

app = FastAPI(
    title="CRM API",
    description="Customer registration CRM with Q2 Helix customer/account integration",
    version="0.2.0",
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
app.include_router(q2_accounts.router)
