from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class APIResponse(BaseModel):
    status: str = Field(examples=["success"])
    message: str = Field(examples=["Request completed successfully."])
    timestamp: str
    data: Any = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(APIResponse):
    status: str = Field(default="error")


class HealthPayload(BaseModel):
    service: str
    version: str
    environment: str
    artifacts: dict[str, bool]

