from __future__ import annotations

from fastapi import APIRouter, Depends

from api.dependencies.auth import get_current_principal
from api.schemas.common import APIResponse
from api.services.analytics_service import analytics_service
from api.utils.response import success_response

router = APIRouter(prefix="/analytics", tags=["Analytics"], dependencies=[Depends(get_current_principal)])


@router.get("/overview", response_model=APIResponse, summary="Enterprise analytics overview")
def overview() -> dict:
    payload = analytics_service.overview()
    return success_response(payload["data"], message="Analytics overview returned.", metadata=payload["metadata"])


@router.get("/kpis", response_model=APIResponse, summary="Enterprise KPI list")
def kpis() -> dict:
    payload = analytics_service.kpis()
    return success_response(payload["data"], message="Analytics KPIs returned.", metadata=payload["metadata"])


@router.get("/summary", response_model=APIResponse, summary="Artifact and capability summary")
def summary() -> dict:
    payload = analytics_service.summary()
    return success_response(payload["data"], message="Analytics summary returned.", metadata=payload["metadata"])

