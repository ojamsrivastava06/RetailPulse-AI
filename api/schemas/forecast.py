from __future__ import annotations

from pydantic import BaseModel


class ForecastFilters(BaseModel):
    product: str | None = None
    country: str | None = None
    category: str | None = None
    model: str | None = None
    horizon_days: int | None = None
    forecast_level: str | None = None

