"""Q2 Helix integration — connection structure owned by q2-authentication."""

from james.ext.q2.client import HelixClient
from james.ext.q2.config import Q2Config, get_q2_config

__all__ = ["HelixClient", "Q2Config", "get_q2_config"]
