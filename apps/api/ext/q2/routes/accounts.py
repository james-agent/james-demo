"""Thin operator routes for Helix account operations."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from ext.q2.client import HelixClient
from ext.q2.config import load_q2_config
from ext.q2.errors import Q2Error, Q2NotFoundError
from ext.q2.schemas import AccountCreateRequest
from ext.q2.services.account import AccountService

router = APIRouter(prefix="/accounts")


@router.post("/create")
def create_account(body: AccountCreateRequest) -> dict[str, Any]:
    config = load_q2_config()
    client = HelixClient(config)
    try:
        return AccountService(client).create(body.model_dump())
    except Q2Error as exc:
        raise HTTPException(status_code=exc.http_status or 502, detail={"code": exc.code, "message": exc.message}) from exc
    finally:
        client.close()


@router.get("/by-tag/{tag}")
def get_account_by_tag(tag: str) -> dict[str, Any]:
    config = load_q2_config()
    client = HelixClient(config)
    try:
        return AccountService(client).get_by_tag(tag)
    except Q2NotFoundError as exc:
        raise HTTPException(status_code=404, detail={"code": exc.code, "message": exc.message}) from exc
    except Q2Error as exc:
        raise HTTPException(status_code=exc.http_status or 502, detail={"code": exc.code, "message": exc.message}) from exc
    finally:
        client.close()


@router.get("/customer/{customer_id}")
def list_accounts_for_customer(customer_id: str) -> dict[str, Any]:
    config = load_q2_config()
    client = HelixClient(config)
    try:
        return AccountService(client).list_by_customer(customer_id)
    except Q2Error as exc:
        raise HTTPException(status_code=exc.http_status or 502, detail={"code": exc.code, "message": exc.message}) from exc
    finally:
        client.close()


@router.get("/{account_id}")
def get_account(account_id: str) -> dict[str, Any]:
    config = load_q2_config()
    client = HelixClient(config)
    try:
        return AccountService(client).get(account_id)
    except Q2Error as exc:
        raise HTTPException(status_code=exc.http_status or 502, detail={"code": exc.code, "message": exc.message}) from exc
    finally:
        client.close()
