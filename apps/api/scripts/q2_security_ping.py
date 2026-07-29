#!/usr/bin/env python3
"""Security API gate (PING) for /api/v1/q2/* operator surface.

Validates that the health endpoint responds and never echoes secrets.
Exit 0 on PASS, 2 on CONFIG_ERROR-style failures, 3 on other failures.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

# Isolate gate from platform DATABASE_URL.
os.environ.setdefault("POSTGRES_PASSWORD", "crm_dev_password")
os.environ.setdefault("CRM_DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("Q2_MOCK_MODE", "true")
os.environ.setdefault("Q2_HELIX_API_KEY", "ping-key")
os.environ.setdefault("Q2_HELIX_API_SECRET", "ping-secret-do-not-leak")
os.environ.setdefault("Q2_HELIX_PROGRAM_ID", "ping-program")

from fastapi.testclient import TestClient  # noqa: E402

from crm_api.main import app  # noqa: E402
from ext.q2.config import clear_q2_config_cache  # noqa: E402
from ext.q2.db import reset_db_caches  # noqa: E402


FORBIDDEN_SNIPPETS = (
    "ping-secret-do-not-leak",
    "api_secret",
    "authorization",
)


def main() -> int:
    clear_q2_config_cache()
    reset_db_caches()
    client = TestClient(app)
    response = client.get("/api/v1/q2/health")
    body = response.text
    payload = response.json()

    if response.status_code != 200:
        print(json.dumps({"result": "API_BUSINESS_ERROR", "status_code": response.status_code}, indent=2))
        return 3

    lowered = body.lower()
    leaks = [s for s in FORBIDDEN_SNIPPETS if s in lowered]
    if leaks:
        print(json.dumps({"result": "API_BUSINESS_ERROR", "message": "Secret leakage detected", "leaks": leaks}, indent=2))
        return 3

    if payload.get("code") == "CONFIG_ERROR":
        print(json.dumps({"result": "CONFIG_ERROR", "health": payload}, indent=2))
        return 2

    if not payload.get("ok"):
        print(json.dumps({"result": "API_BUSINESS_ERROR", "health": payload}, indent=2))
        return 3

    print(json.dumps({"result": "PASS", "endpoint": "/api/v1/q2/health", "ok": True}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
