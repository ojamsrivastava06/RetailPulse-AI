from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

from api.core.logging import get_logger
from api.utils.response import error_response

logger = get_logger(__name__)


class RetailPulseAPIException(Exception):
    def __init__(
        self,
        message: str,
        *,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


def _metadata(request: Request, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    metadata = {"request_id": getattr(request.state, "request_id", None), "path": request.url.path}
    metadata.update(extra or {})
    return metadata


async def retailpulse_exception_handler(request: Request, exc: RetailPulseAPIException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(message=exc.message, metadata=_metadata(request, exc.details)),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    message = str(exc.detail) if exc.detail else "HTTP error."
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(message=message, metadata=_metadata(request)),
        headers=exc.headers,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=error_response(
            message="Request validation failed.",
            data={"errors": exc.errors()},
            metadata=_metadata(request),
        ),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled API error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content=error_response(message="Unexpected server error.", metadata=_metadata(request)),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RetailPulseAPIException, retailpulse_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

