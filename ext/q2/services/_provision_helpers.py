"""Pure helpers for customer/account provisioning (no I/O)."""

from __future__ import annotations

from typing import Any

from ext.q2.models.local_customer import LocalCustomer


def split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split(None, 1)
    if not parts:
        return "Customer", "Unknown"
    if len(parts) == 1:
        return parts[0], parts[0]
    return parts[0], parts[1]


def account_tag_for(customer: LocalCustomer) -> str:
    return f"{customer.tag}-acct"[:50]


def extract_customer_id(payload: dict[str, Any]) -> str | None:
    for key in ("customerId", "customer_id", "id"):
        value = payload.get(key)
        if value is not None and str(value).strip():
            return str(value)
    return None


def extract_accounts(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("accounts", "accountList", "data"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict) and "accounts" in value:
            nested = value.get("accounts")
            if isinstance(nested, list):
                return [item for item in nested if isinstance(item, dict)]
    if "accountId" in payload:
        return [payload]
    return []


def is_open_account(account: dict[str, Any]) -> bool:
    status = str(account.get("status") or account.get("accountStatus") or "").strip().lower()
    return status in {"open", "active"} or status == ""


def product_matches(account: dict[str, Any], product_id: str | None) -> bool:
    if not product_id:
        return True
    raw = account.get("productId", account.get("product_id"))
    if raw is None:
        return False
    return str(raw) == str(product_id)


def find_open_account(
    accounts: list[dict[str, Any]],
    product_id: str | None,
) -> dict[str, Any] | None:
    for account in accounts:
        if is_open_account(account) and product_matches(account, product_id):
            return account
    if product_id:
        return None
    for account in accounts:
        if is_open_account(account):
            return account
    return None
