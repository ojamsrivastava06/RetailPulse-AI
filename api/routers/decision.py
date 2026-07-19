from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from api.dependencies.auth import get_current_principal
from api.schemas.common import APIResponse
from api.services.decision_service import decision_service
from api.utils.response import success_response
from api.utils.validation import bounded_limit, normalize_offset

router = APIRouter(prefix="/decision", tags=["Decision Intelligence"], dependencies=[Depends(get_current_principal)])


@router.get("", response_model=APIResponse, summary="Decision intelligence")
def get_decisions(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    domain: str | None = Query(None),
    decision_type: str | None = Query(None),
    priority_band: str | None = Query(None),
    risk_level: str | None = Query(None),
    time_sensitivity: str | None = Query(None),
) -> dict:
    payload = decision_service.get_decisions(
        limit=bounded_limit(limit),
        offset=normalize_offset(offset),
        domain=domain,
        decision_type=decision_type,
        priority_band=priority_band,
        risk_level=risk_level,
        time_sensitivity=time_sensitivity,
    )
    return success_response(payload["data"], message="Decision intelligence returned.", metadata=payload["metadata"])


@router.get("/alerts", response_model=APIResponse, summary="Business alerts")
def get_alerts(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    severity: str | None = Query(None),
    domain: str | None = Query(None),
) -> dict:
    payload = decision_service.get_alerts(
        limit=bounded_limit(limit),
        offset=normalize_offset(offset),
        severity=severity,
        domain=domain,
    )
    return success_response(payload["data"], message="Decision alerts returned.", metadata=payload["metadata"])


@router.get("/scenarios", response_model=APIResponse, summary="Decision scenarios")
def get_scenarios(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    risk_level: str | None = Query(None),
) -> dict:
    payload = decision_service.get_scenarios(
        limit=bounded_limit(limit),
        offset=normalize_offset(offset),
        risk_level=risk_level,
    )
    return success_response(payload["data"], message="Decision scenarios returned.", metadata=payload["metadata"])


@router.get("/recommendations", response_model=APIResponse, summary="Decision recommendations")
def get_recommendations(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    domain: str | None = Query(None),
    time_sensitivity: str | None = Query(None),
) -> dict:
    payload = decision_service.get_recommendations(
        limit=bounded_limit(limit),
        offset=normalize_offset(offset),
        domain=domain,
        time_sensitivity=time_sensitivity,
    )
    return success_response(payload["data"], message="Decision recommendations returned.", metadata=payload["metadata"])


@router.get("/executive", response_model=APIResponse, summary="Executive decision summary")
def get_executive(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    priority: str | None = Query(None),
) -> dict:
    payload = decision_service.get_executive(
        limit=bounded_limit(limit),
        offset=normalize_offset(offset),
        priority=priority,
    )
    return success_response(payload["data"], message="Executive decision summary returned.", metadata=payload["metadata"])

