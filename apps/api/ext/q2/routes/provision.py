"""Operator provision endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ext.q2.client import HelixClient
from ext.q2.config import load_q2_config
from ext.q2.db import get_db_session
from ext.q2.errors import Q2ConfigError, Q2Error
from ext.q2.repositories.provision_runs import ProvisionRunRepository
from ext.q2.schemas import ProvisionRequest, ProvisionRunResponse
from ext.q2.services.provision import ProvisionService

router = APIRouter()


def _to_response(run) -> ProvisionRunResponse:
    return ProvisionRunResponse(
        id=run.id,
        status=run.status,
        total_customers=run.total_customers,
        succeeded_count=run.succeeded_count,
        failed_count=run.failed_count,
        skipped_count=run.skipped_count,
        error_summary=run.error_summary,
        started_at=run.started_at,
        finished_at=run.finished_at,
        created_at=run.created_at,
    )


@router.post("/provision", response_model=ProvisionRunResponse)
def start_provision(
    body: ProvisionRequest | None = None,
    session: Session = Depends(get_db_session),
) -> ProvisionRunResponse:
    body = body or ProvisionRequest()
    config = load_q2_config()
    client = HelixClient(config)
    try:
        client.ensure_configured()
        service = ProvisionService(session, client=client, config=config)
        run = service.run_provision(
            local_customer_keys=body.local_customer_keys,
            sync_from_crm=body.sync_from_crm,
        )
        return _to_response(run)
    except Q2ConfigError as exc:
        raise HTTPException(status_code=503, detail={"code": exc.code, "message": exc.message, **exc.details}) from exc
    except Q2Error as exc:
        raise HTTPException(status_code=502, detail={"code": exc.code, "message": exc.message}) from exc
    finally:
        client.close()


@router.get("/provision/{run_id}", response_model=ProvisionRunResponse)
def get_provision_run(run_id: str, session: Session = Depends(get_db_session)) -> ProvisionRunResponse:
    run = ProvisionRunRepository(session).get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Provision run not found")
    return _to_response(run)
