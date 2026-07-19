from __future__ import annotations

from pydantic import BaseModel


class InventoryFilters(BaseModel):
    product: str | None = None
    country: str | None = None
    category: str | None = None
    warehouse: str | None = None
    risk_level: str | None = None
    horizon_days: int | None = None

