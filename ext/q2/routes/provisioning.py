"""Server-side provisioning APIs for local → Helix customer/account sync."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ext.q2.db import get_db_session, init_db
from ext.q2.repository.customers import LocalCustomerRepository
from ext.q2.services.provisioner import CustomerAccountProvisioner, ProvisionOutcome

router = APIRouter(prefix="/api/v1/q2/provisioning", tags=["q2-provisioning"])

_db_ready = False


def _ensure_db() -> None:
    global _db_ready
    if not _db_ready:
        init_db(create_tables=True)
        _db_ready = True


def get_provisioner(session: Session = Depends(get_db_session)) -> Iterator[CustomerAccountProvisioner]:
    _ensure_db()
    repo = LocalCustomerRepository(session)
    provisioner = CustomerAccountProvisioner(repo)
    try:
        yield provisioner
    finally:
        provisioner.close()


def _serialize_result(result: Any) -> dict[str, Any]:
    data = asdict(result)
    if isinstance(data.get("outcome"), ProvisionOutcome):
        data["outcome"] = data["outcome"].value
    elif hasattr(data.get("outcome"), "value"):
        data["outcome"] = data["outcome"].value
    return data


@router.post("/customers/sync")
def sync_all_customers(
    provisioner: CustomerAccountProvisioner = Depends(get_provisioner),
) -> dict[str, Any]:
    """Idempotently provision every active local customer into Helix."""
    try:
        bulk = provisioner.sync_all()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "processed": bulk.processed,
        "succeeded": bulk.succeeded,
        "failed": bulk.failed,
        "results": [_serialize_result(item) for item in bulk.results],
    }


@router.post("/customers/{local_id}/sync")
def sync_one_customer(
    local_id: uuid.UUID,
    provisioner: CustomerAccountProvisioner = Depends(get_provisioner),
) -> dict[str, Any]:
    """Idempotently provision a single local customer by id."""
    try:
        result = provisioner.sync_one(local_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    payload = _serialize_result(result)
    if result.outcome == ProvisionOutcome.FAILED and result.detail == "Local customer not found":
        raise HTTPException(status_code=404, detail=result.detail)
    return payload
