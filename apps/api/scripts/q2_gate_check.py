#!/usr/bin/env python3
"""Q2 Helix Gate A/C connectivity check.

Exit codes:
  0 PASS
  2 CONFIG_ERROR
  3 API_BUSINESS_ERROR / connectivity failure
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow running from repo root or apps/api.
API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from ext.q2.client import HelixClient  # noqa: E402
from ext.q2.config import REQUIRED_ENV_KEYS, load_q2_config  # noqa: E402
from ext.q2.errors import Q2ConfigError, Q2Error  # noqa: E402


def _status_line(key: str, value: str) -> str:
    return f"  {key}: {value}"


def main() -> int:
    config = load_q2_config()
    print("Q2 Gate Check")
    print("=============")
    print(_status_line("environment", config.environment))
    print(_status_line("api_url", config.api_url or "(empty)"))
    print(_status_line("mock_mode", str(config.mock_mode)))
    print("Credentials:")
    for key in REQUIRED_ENV_KEYS:
        present = bool(getattr(config, {
            "Q2_HELIX_API_URL": "api_url",
            "Q2_HELIX_API_KEY": "api_key",
            "Q2_HELIX_API_SECRET": "api_secret",
            "Q2_HELIX_PROGRAM_ID": "program_id",
        }[key]))
        print(_status_line(key, "SET" if present else "MISSING"))

    if config.missing_keys and not config.mock_mode:
        payload = {
            "result": "CONFIG_ERROR",
            "missing_keys": config.missing_keys,
            "message": "Missing required Q2 Helix environment variables.",
        }
        print(json.dumps(payload, indent=2))
        return 2

    client = HelixClient(config)
    try:
        connectivity = client.test_connectivity()
        payload = {"result": "PASS", "connectivity": connectivity}
        print(json.dumps(payload, indent=2))
        return 0
    except Q2ConfigError as exc:
        print(json.dumps({"result": "CONFIG_ERROR", "message": exc.message, **exc.details}, indent=2))
        return 2
    except Q2Error as exc:
        print(json.dumps({"result": "API_BUSINESS_ERROR", "code": exc.code, "message": exc.message}, indent=2))
        return 3
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
