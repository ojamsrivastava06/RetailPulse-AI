from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from api.dependencies.auth import get_current_principal
from api.schemas.common import APIResponse
from api.services.inventory_service import inventory_service
from api.utils.response import success_response
from api.utils.validation import bounded_limit, normalize_offset

router = APIRouter(prefix="/inventory", tags=["Inventory"], dependencies=[Depends(get_current_principal)])


@router.get("", response_model=APIResponse, summary="Inventory optimization dataset")
def get_inventory(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    product: str | None = Query(None),
    country: str | None = Query(None),
    category: str | None = Query(None),
    warehouse: str | None = Query(None),
    risk_level: str | None = Query(None),
    horizon_days: int | None = Query(None),
) -> dict:
    payload = inventory_service.get_inventory(
        limit=bounded_limit(limit),
        offset=normalize_offset(offset),
        product=product,
        country=country,
        category=category,
        warehouse=warehouse,
        risk_level=risk_level,
        horizon_days=horizon_days,
    )
    return success_response(payload["data"], message="Inventory records returned.", metadata=payload["metadata"])


@router.get("/recommendations", response_model=APIResponse, summary="Inventory recommendations")
def get_recommendations(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    priority: str | None = Query(None),
) -> dict:
    payload = inventory_service.get_recommendations(limit=bounded_limit(limit), offset=normalize_offset(offset), priority=priority)
    return success_response(payload["data"], message="Inventory recommendations returned.", metadata=payload["metadata"])


@router.get("/risk", response_model=APIResponse, summary="Inventory risk")
def get_risk(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    risk_level: str | None = Query(None),
) -> dict:
    payload = inventory_service.get_risk(limit=bounded_limit(limit), offset=normalize_offset(offset), risk_level=risk_level)
    return success_response(payload["data"], message="Inventory risk returned.", metadata=payload["metadata"])


@router.get("/abc", response_model=APIResponse, summary="ABC analysis")
def get_abc(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    abc_class: str | None = Query(None),
) -> dict:
    payload = inventory_service.get_abc(limit=bounded_limit(limit), offset=normalize_offset(offset), abc_class=abc_class)
    return success_response(payload["data"], message="ABC analysis returned.", metadata=payload["metadata"])


@router.get("/xyz", response_model=APIResponse, summary="XYZ analysis")
def get_xyz(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    xyz_class: str | None = Query(None),
) -> dict:
    payload = inventory_service.get_xyz(limit=bounded_limit(limit), offset=normalize_offset(offset), xyz_class=xyz_class)
    return success_response(payload["data"], message="XYZ analysis returned.", metadata=payload["metadata"])

