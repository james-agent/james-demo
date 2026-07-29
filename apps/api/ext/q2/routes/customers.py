"""Thin operator routes for Helix customer operations."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from ext.q2.client import HelixClient
from ext.q2.config import load_q2_config
from ext.q2.errors import Q2Error, Q2NotFoundError
from ext.q2.schemas import CustomerOnboardRequest
from ext.q2.services.customer import CustomerService

router = APIRouter(prefix="/customers")


@router.post("/onboard")
def onboard_customer(body: CustomerOnboardRequest) -> dict[str, Any]:
    config = load_q2_config()
    client = HelixClient(config)
    try:
        payload = body.model_dump(exclude={"extra"})
        payload.update(body.extra)
        payload = {k: v for k, v in payload.items() if v is not None}
        return CustomerService(client).onboard(payload)
    except Q2Error as exc:
        raise HTTPException(status_code=exc.http_status or 502, detail={"code": exc.code, "message": exc.message}) from exc
    finally:
        client.close()


@router.get("/by-tag/{tag}")
def get_customer_by_tag(tag: str) -> dict[str, Any]:
    config = load_q2_config()
    client = HelixClient(config)
    try:
        return CustomerService(client).get_by_tag(tag)
    except Q2NotFoundError as exc:
        raise HTTPException(status_code=404, detail={"code": exc.code, "message": exc.message}) from exc
    except Q2Error as exc:
        raise HTTPException(status_code=exc.http_status or 502, detail={"code": exc.code, "message": exc.message}) from exc
    finally:
        client.close()


@router.get("/{customer_id}")
def get_customer(customer_id: str) -> dict[str, Any]:
    config = load_q2_config()
    client = HelixClient(config)
    try:
        return CustomerService(client).get(customer_id)
    except Q2Error as exc:
        raise HTTPException(status_code=exc.http_status or 502, detail={"code": exc.code, "message": exc.message}) from exc
    finally:
        client.close()
