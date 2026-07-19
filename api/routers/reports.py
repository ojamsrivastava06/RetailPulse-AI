from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse

from api.dependencies.auth import get_current_principal
from api.schemas.common import APIResponse
from api.services.analytics_service import report_service
from api.utils.response import success_response
from api.utils.validation import bounded_limit, ensure_safe_filename, normalize_offset

router = APIRouter(prefix="/reports", tags=["Reports"], dependencies=[Depends(get_current_principal)])


@router.get("", response_model=APIResponse, summary="Report and artifact catalog")
def list_reports() -> dict:
    payload = report_service.list_reports()
    return success_response(payload["data"], message="Report catalog returned.", metadata=payload["metadata"])


@router.get("/download/{filename}", summary="Download generated artifact")
def download_report(filename: str) -> FileResponse:
    safe_name = ensure_safe_filename(filename)
    try:
        path = report_service.resolve_download(safe_name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report artifact not found.") from exc
    return FileResponse(path=path, filename=path.name)


@router.get("/preview/{filename}", response_model=APIResponse, summary="Preview CSV report artifact")
def preview_csv(
    filename: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> dict:
    safe_name = ensure_safe_filename(filename)
    try:
        payload = report_service.preview_csv(safe_name, limit=bounded_limit(limit), offset=normalize_offset(offset))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report artifact not found.") from exc
    return success_response(payload["data"], message="Report preview returned.", metadata=payload["metadata"])

