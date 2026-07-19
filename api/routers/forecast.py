from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from api.dependencies.auth import get_current_principal
from api.schemas.common import APIResponse
from api.services.forecast_service import forecast_service
from api.utils.response import success_response
from api.utils.validation import bounded_limit, normalize_offset

router = APIRouter(prefix="/forecast", tags=["Forecast"], dependencies=[Depends(get_current_principal)])


@router.get(
    "",
    response_model=APIResponse,
    summary="Historical forecast backtest results",
    description="Returns generated forecast backtest rows from processed/forecast_results.csv with optional filters.",
)
def get_forecast(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    product: str | None = Query(None),
    country: str | None = Query(None),
    category: str | None = Query(None),
    model: str | None = Query(None),
) -> dict:
    payload = forecast_service.get_forecast(
        limit=bounded_limit(limit),
        offset=normalize_offset(offset),
        product=product,
        country=country,
        category=category,
        model=model,
    )
    return success_response(payload["data"], message="Forecast results returned.", metadata=payload["metadata"])


@router.get(
    "/leaderboard",
    response_model=APIResponse,
    summary="Forecast model leaderboard",
    description="Returns the generated model leaderboard ranked by eligibility and forecast error.",
)
def get_leaderboard(limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)) -> dict:
    payload = forecast_service.get_leaderboard(limit=bounded_limit(limit), offset=normalize_offset(offset))
    return success_response(payload["data"], message="Forecast leaderboard returned.", metadata=payload["metadata"])


@router.get(
    "/metrics",
    response_model=APIResponse,
    summary="Forecast model metrics",
    description="Returns per-series forecast metrics from processed/forecast_metrics.csv.",
)
def get_metrics(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    model: str | None = Query(None),
    status: str | None = Query(None),
) -> dict:
    payload = forecast_service.get_metrics(
        limit=bounded_limit(limit),
        offset=normalize_offset(offset),
        model=model,
        status=status,
    )
    return success_response(payload["data"], message="Forecast metrics returned.", metadata=payload["metadata"])


@router.get(
    "/future",
    response_model=APIResponse,
    summary="Future demand forecast",
    description="Returns generated future predictions from processed/future_predictions.csv.",
)
def get_future(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    product: str | None = Query(None),
    country: str | None = Query(None),
    category: str | None = Query(None),
    model: str | None = Query(None),
    horizon_days: int | None = Query(None),
    forecast_level: str | None = Query(None),
) -> dict:
    payload = forecast_service.get_future(
        limit=bounded_limit(limit),
        offset=normalize_offset(offset),
        product=product,
        country=country,
        category=category,
        model=model,
        horizon_days=horizon_days,
        forecast_level=forecast_level,
    )
    return success_response(payload["data"], message="Future forecast returned.", metadata=payload["metadata"])

