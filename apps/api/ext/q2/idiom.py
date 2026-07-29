"""Operator-facing idiom for the Q2 Helix integration.

JAMES_AGENTIC_IDIOM requires English (`en`) for API messages, docs, and
operator-visible strings in this package.
"""

from __future__ import annotations

LOCALE = "en"
LANGUAGE_NAME = "English"

# Stable English copy reused by gates/routes (keep ASCII; no localized variants).
MSG_MISSING_HELIX_ENV = "Missing required Q2 Helix environment variables."
MSG_PROVISION_RUN_NOT_FOUND = "Provision run not found"
MSG_HELIX_BUSINESS_ERROR = "Helix business error"
MSG_NON_JSON_RESPONSE = "Helix returned non-JSON response."
