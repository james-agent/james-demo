"""Q2 Helix Gate A / Gate C connectivity check.

Loads Q2 config, reports SET/MISSING (never secret values), tests connectivity,
discovers program/products, and classifies PASS | CONFIG_ERROR | API_BUSINESS_ERROR.

Usage (from repository root)::

    python3 scripts/q2_gate_check.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ext.q2.client import HelixAPIError, HelixClient  # noqa: E402
from ext.q2.config import get_q2_config  # noqa: E402

# Clear cached config so a fresh .env is always respected when the script runs.
get_q2_config.cache_clear()


def _print_header() -> None:
    print("Q2 Helix Gate Check")
    print("=" * 40)


def main() -> int:
    _print_header()
    config = get_q2_config()

    print("Environment:", config.environment)
    print("API URL:", config.api_url)
    print("Credential status:")
    for name, status in config.status_map().items():
        print(f"  {name}: {status}")

    missing = config.missing_fields()
    if missing:
        print()
        print("RESULT: CONFIG_ERROR")
        print("Missing required variables:", ", ".join(missing))
        print()
        print("Template (.env):")
        print("  Q2_HELIX_API_URL=https://sandbox-api.helix.q2.com")
        print("  Q2_HELIX_API_KEY=<api-key>")
        print("  Q2_HELIX_API_SECRET=<api-secret>")
        print("  Q2_HELIX_PROGRAM_ID=<program-id>")
        print("  Q2_ENVIRONMENT=sandbox")
        print()
        print("Notes:")
        print("  - HTTP Basic Auth: username=API Key, password=API Secret")
        print("  - Production requires IP whitelisting (sandbox whitelist may differ)")
        print("  - Never commit real credentials; keep them in .env only")
        return 2

    try:
        with HelixClient(config) as client:
            print()
            print("Testing connectivity (GET /)...")
            welcome = client.test_connectivity()
            welcome_summary = (
                welcome.get("message")
                or welcome.get("welcome")
                or (list(welcome.keys()) if isinstance(welcome, dict) else type(welcome).__name__)
            )
            print("  Connectivity: OK")
            print("  Welcome payload keys/message:", welcome_summary)

            print()
            print("Discovering program (POST /program/get)...")
            program = client.get_program()
            data = program.get("data", program) if isinstance(program, dict) else {}
            program_name = data.get("name") or data.get("programName") or config.program_id
            products = client.discover_products(program)
            product_ids = [
                str(p.get("productId") or p.get("id") or p.get("name") or "unknown") for p in products
            ]
            print(f"  Program: {program_name}")
            print(f"  Products discovered: {len(products)}")
            if product_ids:
                print("  Product ids:", ", ".join(product_ids[:20]))
                if len(product_ids) > 20:
                    print(f"  ... and {len(product_ids) - 20} more")

        print()
        print("RESULT: PASS")
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "environment": config.environment,
                    "api_url": config.api_url,
                    "program_id": config.program_id,
                    "product_count": len(products),
                },
                indent=2,
            )
        )
        print()
        print("Ops notes:")
        print("  - IP whitelisting is required for production; contact Q2/Helix support")
        print("  - Rate limits: respect HTTP 429; prefer connection reuse (client pooling)")
        print("  - Q2 requires middleware-only access (no direct browser calls)")
        return 0

    except HelixAPIError as exc:
        print()
        print(f"RESULT: {exc.classification}")
        print(f"Detail: {exc}")
        if exc.status_code is not None:
            print(f"HTTP status: {exc.status_code}")
        return 1 if exc.classification == "API_BUSINESS_ERROR" else 2
    except Exception as exc:  # noqa: BLE001 — gate script must never crash silently
        print()
        print("RESULT: CONFIG_ERROR")
        print(f"Unexpected error: {exc.__class__.__name__}: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
