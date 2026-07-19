from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd


def read_csv(path: Path, parse_dates: Sequence[str] = ()) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, parse_dates=[column for column in parse_dates if column])
    except Exception:
        return pd.DataFrame()


def numeric_series(frame: pd.DataFrame, column: str, default: float = 0.0) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype="float64")
    return pd.to_numeric(frame[column], errors="coerce").fillna(default).astype(float)


def text_series(frame: pd.DataFrame, column: str, default: str = "") -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype="object")
    return frame[column].fillna(default).astype(str)


def coalesce_numeric(frame: pd.DataFrame, columns: Sequence[str], default: float = 0.0) -> pd.Series:
    result = pd.Series(np.nan, index=frame.index, dtype="float64")
    for column in columns:
        if column in frame.columns:
            result = result.fillna(pd.to_numeric(frame[column], errors="coerce"))
    return result.fillna(default).astype(float)


def coalesce_text(frame: pd.DataFrame, columns: Sequence[str], default: str = "") -> pd.Series:
    result = pd.Series("", index=frame.index, dtype="object")
    for column in columns:
        if column in frame.columns:
            candidate = frame[column].fillna("").astype(str)
            result = result.mask(result.eq(""), candidate)
    return result.replace("", default)


def normalize_score(values: pd.Series, *, floor: float = 0.0, ceiling: float = 100.0) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce").fillna(0.0).astype(float)
    minimum = numeric.min()
    maximum = numeric.max()
    if pd.isna(minimum) or pd.isna(maximum) or minimum == maximum:
        return pd.Series((floor + ceiling) / 2, index=values.index, dtype="float64")
    scaled = (numeric - minimum) / (maximum - minimum)
    return (scaled * (ceiling - floor) + floor).clip(floor, ceiling)


def clip_score(values: pd.Series | float, *, lower: float = 0.0, upper: float = 100.0) -> pd.Series | float:
    if isinstance(values, pd.Series):
        return pd.to_numeric(values, errors="coerce").fillna(0.0).clip(lower, upper)
    return float(max(lower, min(upper, values)))


def safe_divide(numerator: pd.Series | float, denominator: pd.Series | float, default: float = 0.0):
    with np.errstate(divide="ignore", invalid="ignore"):
        result = np.divide(numerator, denominator)
    if isinstance(result, pd.Series):
        return result.replace([np.inf, -np.inf], np.nan).fillna(default)
    if isinstance(result, np.ndarray):
        return pd.Series(result).replace([np.inf, -np.inf], np.nan).fillna(default)
    if pd.isna(result) or result in (np.inf, -np.inf):
        return default
    return result


def risk_level(score: float) -> str:
    if score >= 80:
        return "Critical"
    if score >= 65:
        return "High"
    if score >= 45:
        return "Medium"
    return "Low"


def priority_level(score: float) -> str:
    if score >= 85:
        return "P0"
    if score >= 70:
        return "P1"
    if score >= 50:
        return "P2"
    return "P3"


def time_sensitivity(score: float) -> str:
    if score >= 85:
        return "Immediate"
    if score >= 70:
        return "This Week"
    if score >= 50:
        return "This Month"
    return "Monitor"


def format_currency(value: float) -> str:
    return f"${float(value):,.0f}"


def format_percent(value: float) -> str:
    return f"{float(value):.1%}"


def top_n(frame: pd.DataFrame, sort_columns: Iterable[str], n: int) -> pd.DataFrame:
    columns = [column for column in sort_columns if column in frame.columns]
    if frame.empty or not columns:
        return frame.head(n).copy()
    return frame.sort_values(columns, ascending=[False] * len(columns)).head(n).copy()


def add_decision_ids(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.reset_index(drop=True).copy()
    data.insert(0, "DecisionID", [f"DI-{index + 1:05d}" for index in range(len(data))])
    return data
