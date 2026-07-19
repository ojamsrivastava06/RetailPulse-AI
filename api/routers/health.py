from __future__ import annotations

from fastapi import APIRouter, Depends

from api.core.config import get_settings
from api.dependencies.database import ArtifactDataSource, get_data_source
from api.schemas.common import APIResponse
from api.utils.response import success_response

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=APIResponse,
    summary="Health check",
    description="Returns a lightweight service liveness response without requiring authentication.",
)
def health(data_source: ArtifactDataSource = Depends(get_data_source)) -> dict:
    settings = get_settings()
    return success_response(
        {
            "service": settings.app_name,
            "version": settings.version,
            "environment": settings.environment,
            "artifacts": data_source.status,
        },
        message="RetailPulse API is healthy.",
    )


@router.get(
    "/version",
    response_model=APIResponse,
    summary="API version",
    description="Returns API version and runtime environment metadata.",
)
def version() -> dict:
    settings = get_settings()
    return success_response(
        {"name": settings.app_name, "version": settings.version, "environment": settings.environment},
        message="RetailPulse API version resolved.",
    )


@router.get(
    "/status",
    response_model=APIResponse,
    summary="Artifact status",
    description="Reports whether the read-only artifact directories used by the API are available.",
)
def status(data_source: ArtifactDataSource = Depends(get_data_source)) -> dict:
    settings = get_settings()
    return success_response(
        data_source.status,
        message="RetailPulse artifact status resolved.",
        metadata={
            "project_root": str(settings.project_root),
            "processed": str(settings.processed_output_dir),
            "reports": str(settings.reports_dir),
            "models": str(settings.models_dir),
        },
    )

