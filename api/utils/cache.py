from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from api.core.config import APISettings, get_settings
from api.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class DatasetSpec:
    key: str
    path: Path
    parse_dates: tuple[str, ...] = ()


def dataset_specs(settings: APISettings | None = None) -> dict[str, DatasetSpec]:
    settings = settings or get_settings()
    processed = settings.processed_output_dir
    curated = settings.processed_data_dir
    return {
        "sales": DatasetSpec("sales", curated / "final_processed_dataset.csv", ("InvoiceDate",)),
        "forecast_results": DatasetSpec("forecast_results", processed / "forecast_results.csv", ("Date",)),
        "leaderboard": DatasetSpec("leaderboard", processed / "leaderboard.csv"),
        "forecast_metrics": DatasetSpec("forecast_metrics", processed / "forecast_metrics.csv"),
        "future_predictions": DatasetSpec("future_predictions", processed / "future_predictions.csv", ("Date",)),
        "forecast_dashboard": DatasetSpec("forecast_dashboard", processed / "forecast_dashboard.csv"),
        "inventory_dataset": DatasetSpec("inventory_dataset", processed / "inventory_dataset.csv", ("Date",)),
        "inventory_recommendations": DatasetSpec("inventory_recommendations", processed / "inventory_recommendations.csv"),
        "inventory_risk": DatasetSpec("inventory_risk", processed / "inventory_risk.csv"),
        "inventory_metrics": DatasetSpec("inventory_metrics", processed / "inventory_metrics.csv"),
        "inventory_dashboard": DatasetSpec("inventory_dashboard", processed / "inventory_dashboard.csv"),
        "abc_analysis": DatasetSpec("abc_analysis", processed / "abc_analysis.csv"),
        "xyz_analysis": DatasetSpec("xyz_analysis", processed / "xyz_analysis.csv"),
        "abc_xyz_matrix": DatasetSpec("abc_xyz_matrix", processed / "abc_xyz_matrix.csv"),
        "customer_segments": DatasetSpec("customer_segments", processed / "customer_segments.csv", ("FirstPurchase", "LastPurchase")),
        "rfm_table": DatasetSpec("rfm_table", processed / "rfm_table.csv", ("FirstPurchase", "LastPurchase")),
        "customer_metrics": DatasetSpec("customer_metrics", processed / "customer_metrics.csv"),
        "segment_summary": DatasetSpec("segment_summary", processed / "segment_summary.csv"),
        "customer_churn_predictions": DatasetSpec(
            "customer_churn_predictions",
            processed / "customer_churn_predictions.csv",
            ("FirstPurchase", "LastPurchase", "SnapshotDate", "ExpectedNextPurchase"),
        ),
        "customer_health_scores": DatasetSpec("customer_health_scores", processed / "customer_health_scores.csv"),
        "customer_probability_scores": DatasetSpec("customer_probability_scores", processed / "customer_probability_scores.csv"),
        "customer_business_actions": DatasetSpec("customer_business_actions", processed / "customer_business_actions.csv"),
        "customer_model_leaderboard": DatasetSpec("customer_model_leaderboard", processed / "customer_model_leaderboard.csv"),
        "business_decisions": DatasetSpec("business_decisions", processed / "business_decisions.csv"),
        "executive_summary": DatasetSpec("executive_summary", processed / "executive_summary.csv", ("GeneratedAt",)),
        "business_alerts": DatasetSpec("business_alerts", processed / "business_alerts.csv"),
        "priority_actions": DatasetSpec("priority_actions", processed / "priority_actions.csv"),
        "risk_summary": DatasetSpec("risk_summary", processed / "risk_summary.csv"),
        "scenario_analysis": DatasetSpec("scenario_analysis", processed / "scenario_analysis.csv"),
        "recommendation_scores": DatasetSpec("recommendation_scores", processed / "recommendation_scores.csv"),
    }


def _file_signature(path: Path) -> tuple[int, int]:
    if not path.exists():
        return 0, 0
    stat = path.stat()
    return stat.st_mtime_ns, stat.st_size


@lru_cache(maxsize=96)
def _read_csv_cached(
    path_str: str,
    modified_ns: int,
    size: int,
    parse_dates: tuple[str, ...],
) -> pd.DataFrame:
    path = Path(path_str)
    if not path.exists():
        logger.warning("Artifact not found: %s", path)
        return pd.DataFrame()
    try:
        return pd.read_csv(path, parse_dates=list(parse_dates) or None, low_memory=False)
    except Exception:
        logger.exception("Failed to read artifact: %s", path)
        return pd.DataFrame()


def read_csv_artifact(path: Path, parse_dates: Iterable[str] = ()) -> pd.DataFrame:
    modified_ns, size = _file_signature(path)
    return _read_csv_cached(str(path), modified_ns, size, tuple(parse_dates)).copy()


def read_dataset(key: str) -> tuple[pd.DataFrame, DatasetSpec]:
    specs = dataset_specs()
    if key not in specs:
        raise KeyError(f"Unknown dataset key: {key}")
    spec = specs[key]
    return read_csv_artifact(spec.path, spec.parse_dates), spec


def source_metadata(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"source": str(path), "exists": False}
    stat = path.stat()
    return {
        "source": str(path),
        "exists": True,
        "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        "size_bytes": stat.st_size,
    }


def _json_safe_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, pd.Timestamp):
        return None if pd.isna(value) else value.isoformat()
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, np.generic):
        return _json_safe_value(value.item())
    if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
        return None
    if pd.isna(value):
        return None
    return value


def dataframe_to_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    clean = frame.astype(object).where(pd.notna(frame), None)
    records = clean.to_dict(orient="records")
    return [{key: _json_safe_value(value) for key, value in row.items()} for row in records]


def apply_filters(frame: pd.DataFrame, filters: dict[str, Any]) -> pd.DataFrame:
    data = frame
    for column, value in filters.items():
        if value in (None, "", [], ()):
            continue
        if column not in data.columns:
            continue
        values = value if isinstance(value, list) else [value]
        normalized_values = {str(item).strip().lower() for item in values if str(item).strip()}
        if not normalized_values:
            continue
        data = data[data[column].astype(str).str.lower().isin(normalized_values)]
    return data.copy()


def sort_frame(frame: pd.DataFrame, columns: list[str], ascending: bool = True) -> pd.DataFrame:
    sort_columns = [column for column in columns if column in frame.columns]
    if frame.empty or not sort_columns:
        return frame.copy()
    return frame.sort_values(sort_columns, ascending=ascending).copy()


def page_frame(frame: pd.DataFrame, *, limit: int, offset: int) -> pd.DataFrame:
    return frame.iloc[offset : offset + limit].copy()


def frame_payload(
    frame: pd.DataFrame,
    *,
    spec: DatasetSpec,
    limit: int,
    offset: int,
    filters: dict[str, Any] | None = None,
    summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata = {
        **source_metadata(spec.path),
        "dataset": spec.key,
        "total_records": int(len(frame)),
        "returned_records": int(min(max(len(frame) - offset, 0), limit)),
        "limit": limit,
        "offset": offset,
        "columns": list(frame.columns),
        "filters": {key: value for key, value in (filters or {}).items() if value not in (None, "", [], ())},
    }
    if summary:
        metadata["summary"] = summary
    return {"data": dataframe_to_records(page_frame(frame, limit=limit, offset=offset)), "metadata": metadata}


def numeric_sum(frame: pd.DataFrame, column: str) -> float | None:
    if frame.empty or column not in frame.columns:
        return None
    return float(pd.to_numeric(frame[column], errors="coerce").fillna(0.0).sum())


def numeric_mean(frame: pd.DataFrame, column: str) -> float | None:
    if frame.empty or column not in frame.columns:
        return None
    values = pd.to_numeric(frame[column], errors="coerce").dropna()
    if values.empty:
        return None
    return float(values.mean())


def unique_count(frame: pd.DataFrame, column: str) -> int | None:
    if frame.empty or column not in frame.columns:
        return None
    return int(frame[column].nunique(dropna=True))


def count_values(frame: pd.DataFrame, column: str, values: set[str]) -> int | None:
    if frame.empty or column not in frame.columns:
        return None
    normalized = {value.lower() for value in values}
    return int(frame[column].astype(str).str.lower().isin(normalized).sum())


def list_files(directory: Path, suffixes: tuple[str, ...], *, exclude_backups: bool = True) -> list[dict[str, Any]]:
    if not directory.exists():
        return []
    allowed = {suffix.lower() for suffix in suffixes}
    rows: list[dict[str, Any]] = []
    for path in directory.iterdir():
        if not path.is_file():
            continue
        if exclude_backups and ".bak_" in path.name:
            continue
        if path.suffix.lower() not in allowed:
            continue
        stat = path.stat()
        rows.append(
            {
                "filename": path.name,
                "path": str(path),
                "kind": path.suffix.lower().lstrip("."),
                "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            }
        )
    return sorted(rows, key=lambda item: item["modified_at"], reverse=True)
