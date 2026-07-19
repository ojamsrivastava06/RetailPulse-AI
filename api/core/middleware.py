from __future__ import annotations

import time
import uuid
from collections.abc import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from api.core.config import get_settings
from api.core.logging import get_logger
from api.dependencies.rate_limit import get_rate_limiter
from api.utils.response import error_response

logger = get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = str(duration_ms)
        logger.info("%s %s -> %s in %sms", request.method, request.url.path, response.status_code, duration_ms)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    EXCLUDED_PREFIXES = ("/docs", "/redoc", "/openapi.json")
    EXCLUDED_PATHS = {"/", "/health", "/version", "/status"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.method == "OPTIONS" or request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)
        if request.url.path.startswith(self.EXCLUDED_PREFIXES):
            return await call_next(request)

        settings = get_settings()
        api_key = request.headers.get(settings.api_key_header_name, "")
        client_host = request.client.host if request.client else "unknown"
        identity = api_key[:12] if api_key else client_host
        decision = get_rate_limiter().check(f"{identity}:{request.url.path}")
        if not decision.allowed:
            return JSONResponse(
                status_code=429,
                content=error_response(
                    message="Rate limit exceeded.",
                    metadata={
                        "retry_after_seconds": decision.retry_after_seconds,
                        "limit": settings.rate_limit_requests,
                        "window_seconds": settings.rate_limit_window_seconds,
                    },
                ),
                headers={"Retry-After": str(decision.retry_after_seconds)},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(decision.remaining)
        return response

