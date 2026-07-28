"""Q2 Helix connection package — config and HTTP client only.

Owned exclusively by the q2-authentication agent. Implementing agents must
run ``scripts/q2_gate_check.py``; they must not create or edit this package.
"""

from ext.q2.client import HelixClient, HelixAPIError
from ext.q2.config import Q2Config, get_q2_config

__all__ = [
    "HelixAPIError",
    "HelixClient",
    "Q2Config",
    "get_q2_config",
]
