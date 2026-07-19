from __future__ import annotations

from pydantic import BaseModel


class CustomerFilters(BaseModel):
    customer_id: int | None = None
    segment: str | None = None
    tier: str | None = None
    health_band: str | None = None
    risk_category: str | None = None

