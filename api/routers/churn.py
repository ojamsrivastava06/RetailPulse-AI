from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from api.dependencies.auth import get_current_principal
from api.schemas.common import APIResponse
from api.services.churn_service import churn_service
from api.utils.response import success_response
from api.utils.validation import bounded_limit, normalize_offset

router = APIRouter(prefix="/churn", tags=["Churn"], dependencies=[Depends(get_current_principal)])


@router.get("", response_model=APIResponse, summary="Customer churn intelligence")
def get_churn(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    customer_id: int | None = Query(None),
    risk_category: str | None = Query(None),
    health_band: str | None = Query(None),
) -> dict:
    payload = churn_service.get_churn(
        limit=bounded_limit(limit),
        offset=normalize_offset(offset),
        customer_id=customer_id,
        risk_category=risk_category,
        health_band=health_band,
    )
    return success_response(payload["data"], message="Churn intelligence returned.", metadata=payload["metadata"])


@router.get("/predictions", response_model=APIResponse, summary="Churn predictions")
def get_predictions(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    customer_id: int | None = Query(None),
    risk_category: str | None = Query(None),
) -> dict:
    payload = churn_service.get_predictions(
        limit=bounded_limit(limit),
        offset=normalize_offset(offset),
        customer_id=customer_id,
        risk_category=risk_category,
    )
    return success_response(payload["data"], message="Churn predictions returned.", metadata=payload["metadata"])


@router.get("/actions", response_model=APIResponse, summary="Churn retention actions")
def get_actions(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    customer_id: int | None = Query(None),
    risk_category: str | None = Query(None),
    recommended_action: str | None = Query(None),
) -> dict:
    payload = churn_service.get_actions(
        limit=bounded_limit(limit),
        offset=normalize_offset(offset),
        customer_id=customer_id,
        risk_category=risk_category,
        recommended_action=recommended_action,
    )
    return success_response(payload["data"], message="Churn actions returned.", metadata=payload["metadata"])


@router.get("/probabilities", response_model=APIResponse, summary="Churn probability scores")
def get_probabilities(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    customer_id: int | None = Query(None),
    risk_category: str | None = Query(None),
) -> dict:
    payload = churn_service.get_probabilities(
        limit=bounded_limit(limit),
        offset=normalize_offset(offset),
        customer_id=customer_id,
        risk_category=risk_category,
    )
    return success_response(payload["data"], message="Churn probabilities returned.", metadata=payload["metadata"])

