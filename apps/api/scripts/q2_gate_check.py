#!/usr/bin/env python3
"""Q2 Helix connectivity gate check (Gate A / Gate C)."""

from __future__ import annotations

import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from ext.q2.client import Q2HelixClient  # noqa: E402
from ext.q2.config import Q2ConfigError, get_q2_config  # noqa: E402
from ext.q2.exceptions import Q2ApiError  # noqa: E402

REQUIRED_VARS = (
    "Q2_HELIX_API_URL",
    "Q2_HELIX_API_KEY",
    "Q2_HELIX_API_SECRET",
    "Q2_HELIX_PROGRAM_ID",
)


def _report_env(config) -> None:
    print("Q2 Helix Gate Check")
    print("=" * 40)
    print(
        f"  Q2_HELIX_API_URL: {'SET' if config.api_url else 'MISSING'} ({config.api_url or 'n/a'})"
    )
    print(f"  Q2_HELIX_API_KEY: {'SET' if config.api_key.strip() else 'MISSING'}")
    print(f"  Q2_HELIX_API_SECRET: {'SET' if config.api_secret.strip() else 'MISSING'}")
    program_preview = f"{config.program_id[:8]}..." if config.program_id else "n/a"
    print(
        f"  Q2_HELIX_PROGRAM_ID: {'SET' if config.program_id.strip() else 'MISSING'} ({program_preview})"
    )
    print(f"  Q2_ENVIRONMENT: {config.environment}")


def main() -> int:
    config = get_q2_config()
    _report_env(config)

    missing = config.missing_fields()
    if missing:
        print("\nResult: CONFIG_ERROR")
        print(f"Missing: {', '.join(missing)}")
        return 2

    try:
        client = Q2HelixClient(config)
        program = client.test_connectivity()
        program_id = program.get("programId") or program.get("data", {}).get(
            "programId"
        )
        print("\nConnectivity: PASS")
        if program_id:
            print(f"Program ID confirmed: {program_id}")
        print("\nResult: PASS")
        return 0
    except Q2ConfigError as exc:
        print(f"\nResult: CONFIG_ERROR\n{exc}")
        return 2
    except Q2ApiError as exc:
        if exc.status_code in {401, 403}:
            print(f"\nResult: CONFIG_ERROR\nAuthentication failed: {exc}")
            return 2
        print(f"\nResult: API_BUSINESS_ERROR\n{exc}")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
