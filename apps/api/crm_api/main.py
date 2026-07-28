"""CRM API application entrypoint."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure ``ext.q2`` is importable in local (apps/api) and Docker (/app) layouts.
for _root in (Path(__file__).resolve().parents[3], Path(__file__).resolve().parents[1]):
    if (_root / "ext" / "q2").is_dir() and str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
        break

from crm_api.config import get_settings
from crm_api.routes import crm_customers, health
from ext.q2.routes import accounts as q2_accounts
from ext.q2.routes import customers as q2_customers

settings = get_settings()

app = FastAPI(
    title="CRM API",
    description="Customer registration CRM with Q2 Helix middleware integration",
    version="0.1.0",
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
