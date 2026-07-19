from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import HTTPException, Query, status

from api.core.config import get_settings


LimitQuery = Annotated[int, Query(ge=1, description="Maximum records to return.")]
OffsetQuery = Annotated[int, Query(ge=0, description="Number of records to skip.")]


def bounded_limit(limit: int | None) -> int:
    settings = get_settings()
    requested = limit if limit is not None else settings.default_page_size
    return min(max(int(requested), 1), settings.max_page_size)


def normalize_offset(offset: int | None) -> int:
    return max(int(offset or 0), 0)


def parse_csv_values(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def ensure_safe_filename(filename: str) -> str:
    name = Path(filename).name
    if not name or name != filename or ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename.")
    return name

