from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from api.dependencies.auth import get_current_principal
from api.schemas.common import APIResponse
from api.services.customer_service import customer_service
from api.utils.response import success_response
from api.utils.validation import bounded_limit, normalize_offset

router = APIRouter(prefix="/customer", tags=["Customer"], dependencies=[Depends(get_current_principal)])


@router.get("/segments", response_model=APIResponse, summary="Customer segments")
def get_segments(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    customer_id: int | None = Query(None),
    segment: str | None = Query(None),
    tier: str | None = Query(None),
) -> dict:
    payload = customer_service.get_segments(
        limit=bounded_limit(limit),
        offset=normalize_offset(offset),
        customer_id=customer_id,
        segment=segment,
        tier=tier,
    )
    return success_response(payload["data"], message="Customer segments returned.", metadata=payload["metadata"])


@router.get("/rfm", response_model=APIResponse, summary="Customer RFM")
def get_rfm(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    customer_id: int | None = Query(None),
    tier: str | None = Query(None),
) -> dict:
    payload = customer_service.get_rfm(
        limit=bounded_limit(limit),
        offset=normalize_offset(offset),
        customer_id=customer_id,
        tier=tier,
    )
    return success_response(payload["data"], message="Customer RFM returned.", metadata=payload["metadata"])


@router.get("/clv", response_model=APIResponse, summary="Customer lifetime value")
def get_clv(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    customer_id: int | None = Query(None),
) -> dict:
    payload = customer_service.get_clv(limit=bounded_limit(limit), offset=normalize_offset(offset), customer_id=customer_id)
    return success_response(payload["data"], message="Customer CLV returned.", metadata=payload["metadata"])


@router.get("/health", response_model=APIResponse, summary="Customer health scores")
def get_health(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    customer_id: int | None = Query(None),
    health_band: str | None = Query(None),
    risk_category: str | None = Query(None),
) -> dict:
    payload = customer_service.get_health(
        limit=bounded_limit(limit),
        offset=normalize_offset(offset),
        customer_id=customer_id,
        health_band=health_band,
        risk_category=risk_category,
    )
    return success_response(payload["data"], message="Customer health returned.", metadata=payload["metadata"])

