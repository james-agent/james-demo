#!/usr/bin/env python3
"""Q2 Helix Gate A / Gate C connectivity check.

Usage (from repo root or apps/api):
  python3 scripts/q2_gate_check.py
  python3 apps/api/scripts/q2_gate_check.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path


def _ensure_import_path() -> None:
    here = Path(__file__).resolve()
    candidates = [
        here.parent.parent,  # apps/api/scripts -> apps/api
        here.parent.parent / "apps" / "api",  # repo/scripts -> apps/api
    ]
    for path in candidates:
        if (path / "crm_api").is_dir():
            sys.path.insert(0, str(path))
            return


_ensure_import_path()

from crm_api.ext.q2.client import Q2HelixClient, Q2HelixError  # noqa: E402
from crm_api.ext.q2.config import REQUIRED_ENV_KEYS, get_q2_config  # noqa: E402


def _mask(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 4:
        return "****"
    return f"{value[:2]}***{value[-2:]}"


async def run_check() -> dict:
    config = get_q2_config()
    env_report = {
        key: ("SET" if getattr(config, attr) else "MISSING")
        for key, attr in [
            ("Q2_HELIX_API_URL", "api_url"),
            ("Q2_HELIX_API_KEY", "api_key"),
            ("Q2_HELIX_API_SECRET", "api_secret"),
            ("Q2_HELIX_PROGRAM_ID", "program_id"),
        ]
    }
    env_report["Q2_ENVIRONMENT"] = config.environment

    result: dict = {
        "gate": "q2_gate_check",
        "environment": config.environment,
        "base_url": config.base_url,
        "credentials": env_report,
        "program_id_masked": _mask(config.program_id),
        "status": "CONFIG_ERROR",
        "message": "",
        "program": None,
    }

    missing = config.missing_keys()
    if missing:
        result["status"] = "CONFIG_ERROR"
        result["message"] = f"Missing required env vars: {', '.join(missing)}"
        result["required"] = list(REQUIRED_ENV_KEYS)
        return result

    async with Q2HelixClient(config) as client:
        try:
            data = await client.test_connectivity()
            result["status"] = "PASS"
            result["message"] = "Q2 Helix connectivity OK"
            result["program"] = data
            if isinstance(data, dict):
                products = data.get("products") or data.get("Products") or []
                result["products_count"] = len(products) if isinstance(products, list) else None
            return result
        except Q2HelixError as exc:
            if exc.status_code in {400, 404} or exc.helix_status not in (None, 0):
                # Credentials/auth accepted path but business/program issue
                if exc.status_code in {401, 403}:
                    result["status"] = "CONFIG_ERROR"
                else:
                    result["status"] = "API_BUSINESS_ERROR"
            elif exc.status_code in {401, 403, 503}:
                result["status"] = "CONFIG_ERROR"
            else:
                result["status"] = "API_BUSINESS_ERROR"
            result["message"] = exc.message
            result["http_status"] = exc.status_code
            result["helix_status"] = exc.helix_status
            return result


def main() -> int:
    payload = asyncio.run(run_check())
    print(json.dumps(payload, indent=2, default=str))
    status = payload.get("status")
    if status == "PASS":
        return 0
    if status == "API_BUSINESS_ERROR":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
