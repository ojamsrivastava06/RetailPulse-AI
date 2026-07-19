from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Any

import pandas as pd
import streamlit as st

from components.utils import safe_divide


def _unique_values(frame: pd.DataFrame, column: str) -> list[Any]:
    if column not in frame.columns:
        return []
    values = frame[column].dropna().astype(str).unique().tolist()
    return sorted(values)


def categorical_filter(
    frame: pd.DataFrame,
    column: str,
    *,
    label: str | None = None,
    key: str | None = None,
    default_all: bool = True,
    multiselect: bool = True,
) -> tuple[pd.DataFrame, list[str]]:
    if column not in frame.columns:
        return frame, []
    options = _unique_values(frame, column)
    selection: list[str] = [] if default_all else options[:1]
    widget_label = label or column
    if multiselect:
        help_text = "Leave blank to include all values." if default_all else None
        selection = st.multiselect(widget_label, options, default=selection, key=key, help=help_text)
    else:
        selected = st.selectbox(widget_label, ["All", *options], index=0, key=key)
        selection = options if selected == "All" else [selected]
    if selection:
        filtered = frame[frame[column].astype(str).isin(selection)]
    else:
        filtered = frame
    return filtered, selection


def date_range_filter(
    frame: pd.DataFrame,
    column: str,
    *,
    label: str | None = None,
    key: str | None = None,
) -> tuple[pd.DataFrame, tuple[pd.Timestamp | None, pd.Timestamp | None]]:
    if column not in frame.columns or frame.empty:
        return frame, (None, None)
    series = pd.to_datetime(frame[column], errors="coerce")
    valid_dates = series.dropna()
    if valid_dates.empty:
        st.caption(f"{label or column}: no valid dates")
        return frame, (None, None)
    min_date = valid_dates.min().date()
    max_date = valid_dates.max().date()
    selection = st.date_input(label or column, value=(min_date, max_date), key=key)
    if isinstance(selection, tuple) and len(selection) == 2:
        start, end = selection
    else:
        start = end = selection
    start_ts = pd.to_datetime(start) if start else None
    end_ts = pd.to_datetime(end) if end else None
    if start_ts is not None and end_ts is not None:
        filtered = frame[(series >= start_ts) & (series <= end_ts)]
    else:
        filtered = frame
    return filtered, (start_ts, end_ts)


def numeric_range_filter(
    frame: pd.DataFrame,
    column: str,
    *,
    label: str | None = None,
    key: str | None = None,
) -> tuple[pd.DataFrame, tuple[float, float]]:
    if column not in frame.columns or frame.empty:
        return frame, (0.0, 0.0)
    series = pd.to_numeric(frame[column], errors="coerce")
    valid_values = series.dropna()
    if valid_values.empty:
        st.caption(f"{label or column}: no valid values")
        return frame, (0.0, 0.0)
    min_value = float(valid_values.min())
    max_value = float(valid_values.max())
    if min_value == max_value:
        st.caption(f"{label or column}: {min_value:,.2f}")
        return frame, (min_value, max_value)
    selection = st.slider(label or column, min_value=min_value, max_value=max_value, value=(min_value, max_value), key=key)
    filtered = frame[(series >= selection[0]) & (series <= selection[1])]
    return filtered, selection


def render_filter_bar(
    frame: pd.DataFrame,
    *,
    date_column: str | None = None,
    categorical_columns: Sequence[str] = (),
    numeric_columns: Sequence[str] = (),
    key_prefix: str = "",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    filtered = frame.copy()
    selections: dict[str, Any] = {}
    widgets: list[tuple[str, str]] = []
    if date_column:
        widgets.append(("date", date_column))
    widgets.extend(("categorical", column) for column in categorical_columns)
    widgets.extend(("numeric", column) for column in numeric_columns)
    if not widgets:
        return filtered, selections
    row = st.columns(min(len(widgets), 4))
    for index, (widget_type, column) in enumerate(widgets):
        with row[index % len(row)]:
            if widget_type == "date":
                filtered, selection = date_range_filter(filtered, column, label=column.replace("_", " "), key=f"{key_prefix}_{column}")
                selections[column] = selection
            elif widget_type == "categorical":
                filtered, selection = categorical_filter(filtered, column, label=column.replace("_", " "), key=f"{key_prefix}_{column}")
                selections[column] = selection
            elif widget_type == "numeric":
                filtered, selection = numeric_range_filter(filtered, column, label=column.replace("_", " "), key=f"{key_prefix}_{column}")
                selections[column] = selection
    return filtered, selections
