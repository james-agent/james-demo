#!/usr/bin/env python3
"""Q2 Helix Gate A / Gate C check.

Loads Q2 config, reports SET/MISSING for required env vars (never prints secrets),
tests Helix connectivity, and classifies PASS / CONFIG_ERROR / API_BUSINESS_ERROR.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Allow running from repo root without installing the package.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _flag(present: bool) -> str:
    return "SET" if present else "MISSING"


def _scan_codebase(root: Path) -> dict[str, str]:
    checks = {
        "Q2 config": root / "james" / "ext" / "q2" / "config.py",
        "Helix client": root / "james" / "ext" / "q2" / "client.py",
        "Connection routes": root / "james" / "ext" / "q2" / "routes" / "connection.py",
        "Hub app": root / "james" / "hub" / "app.py",
        "Gate script": root / "scripts" / "q2_gate_check.py",
    }
    return {name: ("Present" if path.is_file() else "Missing") for name, path in checks.items()}


def main() -> int:
    from james.ext.q2.client import HelixClient
    from james.ext.q2.config import get_q2_config, reset_q2_config
    from james.ext.q2.errors import Q2APIError, Q2ConfigError, Q2ConnectivityError

    reset_q2_config()
    cfg = get_q2_config()

    print("Q2 Connection Validation Report")
    print("════════════════════════════════")
    print()
    print(f"Environment:     {cfg.q2_environment}")
    print(f"Helix base URL:  {cfg.helix_base_url}")
    print()
    print("Credentials (values never printed):")
    print(f"  Q2_HELIX_API_URL:      {_flag(bool((cfg.q2_helix_api_url or '').strip()))}")
    print(f"  Q2_HELIX_API_KEY:      {_flag(bool(cfg.q2_helix_api_key.strip()))}")
    print(f"  Q2_HELIX_API_SECRET:   {_flag(bool(cfg.q2_helix_api_secret.strip()))}")
    print(f"  Q2_HELIX_PROGRAM_ID:   {_flag(bool(cfg.q2_helix_program_id.strip()))}")
    print(f"  Q2_ENVIRONMENT:        {_flag(bool(cfg.q2_environment))}")
    print(f"  Q2_CALIPER_API_URL:    {_flag(bool(cfg.q2_caliper_api_url.strip()))}")
    print(f"  Q2_CALIPER_API_KEY:    {_flag(bool(cfg.q2_caliper_api_key.strip()))}")
    print(f"  Q2_AMQP_CONNECTION_STRING: {_flag(bool(cfg.q2_amqp_connection_string.strip()))}")
    print()

    components = _scan_codebase(_REPO_ROOT)
    print("Codebase Components:")
    for name, status in components.items():
        mark = "✓" if status == "Present" else "✗"
        print(f"  {mark} {name} — {status}")
    print()

    missing = cfg.missing_helix_vars()
    if missing:
        print("RESULT: CONFIG_ERROR")
        print("Missing required variables:", ", ".join(missing))
        print()
        print("Template (.env):")
        print("  Q2_HELIX_API_URL=https://sandbox-api.helix.q2.com")
        print("  Q2_HELIX_API_KEY=<api-key>")
        print("  Q2_HELIX_API_SECRET=<api-secret>")
        print("  Q2_HELIX_PROGRAM_ID=<program-id>")
        print("  Q2_ENVIRONMENT=sandbox")
        return 2

    detail: dict[str, Any] = {}
    try:
        with HelixClient(cfg) as client:
            try:
                probe = client.test_connectivity()
            except Q2APIError:
                probe = client.get_program()
            else:
                if probe.get("probe") == "root":
                    try:
                        probe = {**probe, "program": client.get_program().get("program")}
                    except Q2APIError as exc:
                        detail["program_error"] = exc.message
            detail["probe"] = probe.get("probe")
            detail["http_status"] = probe.get("http_status")
            program = probe.get("program") if isinstance(probe.get("program"), dict) else None
            if program:
                products = program.get("products") or []
                product_ids = []
                if isinstance(products, list):
                    for item in products:
                        if isinstance(item, dict):
                            pid = item.get("productId") or item.get("product_id")
                            if pid:
                                product_ids.append(str(pid))
                detail["program_id"] = program.get("programId") or program.get("program_id")
                detail["product_count"] = len(product_ids)
                detail["product_ids"] = product_ids[:20]
    except Q2ConfigError as exc:
        print("RESULT: CONFIG_ERROR")
        print(exc.message)
        return 2
    except Q2ConnectivityError as exc:
        print("RESULT: API_BUSINESS_ERROR")
        print(exc.message)
        print("Action: verify Q2_HELIX_API_URL / network / firewall; do not change application code.")
        return 1
    except Q2APIError as exc:
        print("RESULT: API_BUSINESS_ERROR")
        print(exc.message)
        if exc.http_status == 403:
            print("Action: ask Q2 to whitelist this environment's egress IP (sandbox vs production differ).")
        elif exc.http_status == 401:
            print("Action: verify API key/secret in Helix Admin; do not commit secrets.")
        else:
            print("Action: report-only — resolve with Helix Admin / Q2 support.")
        return 1

    print("Helix API:       ✓ Connected")
    print(f"Caliper API:     {'✓ Configured' if cfg.caliper_configured else '✗ Not configured'}")
    print(f"AMQP Events:     {'✓ Configured' if cfg.amqp_configured else '✗ Not configured'}")
    if detail:
        print("Discovery:", json.dumps(detail, indent=2)[:2000])
    print()
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
