from __future__ import annotations

from pydantic import BaseModel


class DecisionFilters(BaseModel):
    domain: str | None = None
    decision_type: str | None = None
    priority_band: str | None = None
    risk_level: str | None = None
    time_sensitivity: str | None = None

