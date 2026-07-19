from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def api_response(
    *,
    status: str,
    message: str,
    data: Any = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "message": message,
        "timestamp": utc_timestamp(),
        "data": data if data is not None else {},
        "metadata": metadata or {},
    }


def success_response(
    data: Any = None,
    *,
    message: str = "Request completed successfully.",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return api_response(status="success", message=message, data=data, metadata=metadata)


def error_response(
    *,
    message: str,
    data: Any = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return api_response(status="error", message=message, data=data, metadata=metadata)

