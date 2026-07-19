from __future__ import annotations

from pydantic import BaseModel


class ChurnFilters(BaseModel):
    customer_id: int | None = None
    risk_category: str | None = None
    health_band: str | None = None
    recommended_action: str | None = None

