from __future__ import annotations

import json
import logging
import math
import shutil
import warnings
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Sequence

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import (
    AdaBoostRegressor,
    ExtraTreesRegressor,
    GradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.feature_selection import RFE
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import ElasticNet, Lasso, LinearRegression, Ridge
from sklearn.metrics import make_scorer, mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, TimeSeriesSplit
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeRegressor

warnings.filterwarnings("ignore")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    from statsmodels.tsa.arima.model import ARIMA as StatsARIMA
    from statsmodels.tsa.holtwinters import ExponentialSmoothing as StatsExponentialSmoothing
    from statsmodels.tsa.holtwinters import Holt as StatsHolt
except Exception:  # pragma: no cover - optional dependency
    StatsARIMA = None
    StatsExponentialSmoothing = None
    StatsHolt = None

try:  # pragma: no cover - optional dependency
    from xgboost import XGBRegressor
except Exception:  # pragma: no cover - optional dependency
    XGBRegressor = None

try:  # pragma: no cover - optional dependency
    from lightgbm import LGBMRegressor
except Exception:  # pragma: no cover - optional dependency
    LGBMRegressor = None

try:  # pragma: no cover - optional dependency
    from catboost import CatBoostRegressor
except Exception:  # pragma: no cover - optional dependency
    CatBoostRegressor = None

try:  # pragma: no cover - optional dependency
    from prophet import Prophet
except Exception:  # pragma: no cover - optional dependency
    Prophet = None

try:  # pragma: no cover - optional dependency
    from pmdarima import auto_arima
except Exception:  # pragma: no cover - optional dependency
    auto_arima = None

try:  # pragma: no cover - optional dependency
    import shap
except Exception:  # pragma: no cover - optional dependency
    shap = None

try:  # pragma: no cover - optional dependency
    import tensorflow as tf
    from tensorflow.keras import callbacks as keras_callbacks
    from tensorflow.keras import layers, models
except Exception:  # pragma: no cover - optional dependency
    tf = None
    keras_callbacks = None
    layers = None
    models = None


SEASON_MAP = {
    12: "Winter",
    1: "Winter",
    2: "Winter",
    3: "Spring",
    4: "Spring",
    5: "Spring",
    6: "Summer",
    7: "Summer",
    8: "Summer",
    9: "Autumn",
    10: "Autumn",
    11: "Autumn",
}
SEASON_CODE = {"Winter": 0, "Spring": 1, "Summer": 2, "Autumn": 3}

LAG_WINDOWS = [1, 3, 7, 14, 21, 30, 60, 90]
ROLLING_MEAN_WINDOWS = [3, 7, 14, 30]
ROLLING_STD_WINDOWS = [7, 14, 30]
DEFAULT_HORIZONS = (30, 60, 90, 180, 365)
DEFAULT_TOP_N_SERIES = 5
DEFAULT_MIN_HISTORY = 180
DEFAULT_TEST_SIZE = 30
MAX_FEATURE_COUNT = 20


@dataclass(frozen=True)
class ModelSpec:
    name: str
    family: str
    available: bool
    factory: Callable[[dict[str, Any] | None], Any] | None = None
    reason_unavailable: str | None = None
    search_strategy: str | None = None
    param_grid: dict[str, Sequence[Any]] = field(default_factory=dict)


@dataclass
class FittedModelBundle:
    model_name: str
    kind: str
    estimator: Any
    feature_columns: list[str]
    selected_features: list[str]
    params: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)


def safe_smape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    actual = np.asarray(y_true, dtype=float)
    predicted = np.asarray(y_pred, dtype=float)
    denom = np.abs(actual) + np.abs(predicted)
    denom = np.where(denom == 0, 1.0, denom)
    return float(np.mean(2.0 * np.abs(predicted - actual) / denom) * 100.0)


def safe_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    actual = np.asarray(y_true, dtype=float)
    predicted = np.asarray(y_pred, dtype=float)
    denom = np.where(np.abs(actual) == 0, 1.0, np.abs(actual))
    return float(np.mean(np.abs((actual - predicted) / denom)) * 100.0)


def mean_absolute_scaled_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    actual = np.asarray(y_true, dtype=float)
    predicted = np.asarray(y_pred, dtype=float)
    if len(actual) < 2:
        return 0.0
    naive_error = np.mean(np.abs(actual[1:] - actual[:-1]))
    if naive_error == 0:
        return 0.0
    return float(np.mean(np.abs(actual - predicted)) / naive_error)


def rmse_metric(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(math.sqrt(mean_squared_error(y_true, y_pred)))


def safe_pct_change(current: float, previous: float) -> float:
    if previous == 0:
        return 0.0 if current == 0 else 1.0
    return float((current - previous) / abs(previous))


def slugify(value: str) -> str:
    filtered = "".join(ch.lower() if ch.isalnum() else "_" for ch in value)
    while "__" in filtered:
        filtered = filtered.replace("__", "_")
    return filtered.strip("_") or "figure"


def json_dumps_safe(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, default=str)


def backup_existing_file(path: Path) -> None:
    if not path.exists():
        return
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    backup_path = path.with_name(f"{path.stem}.bak_{timestamp}{path.suffix}")
    shutil.copy2(path, backup_path)


def write_dataframe(df: pd.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    backup_existing_file(path)
    df.to_csv(path, index=False)
    return path


def write_text(content: str, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    backup_existing_file(path)
    path.write_text(content, encoding="utf-8")
    return path


def write_joblib(payload: Any, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    backup_existing_file(path)
    joblib.dump(payload, path)
    return path


def classify_product(description: str) -> str:
    text = str(description).lower()
    if any(token in text for token in ["light", "lamp", "candlestick", "lantern"]):
        return "Lighting"
    if any(token in text for token in ["frame", "glass", "ornament", "decor", "tree"]):
        return "Decor"
    if any(token in text for token in ["bag", "wallet", "purse", "holder"]):
        return "Accessories"
    if any(token in text for token in ["box", "storage", "jar", "cup", "plate"]):
        return "Homeware"
    if any(token in text for token in ["card", "paper", "stationery"]):
        return "Stationery"
    return "Other"


def build_holiday_flag(series: pd.Series) -> pd.Series:
    flags: list[int] = []
    for dt in pd.to_datetime(series):
        try:
            month = int(dt.month)
            day = int(dt.day)
            is_holiday = (month == 12 and day in {24, 25, 26, 31}) or (month == 1 and day == 1)
            flags.append(int(is_holiday))
        except Exception:
            flags.append(0)
    return pd.Series(flags, index=series.index, dtype=int)


def feature_columns() -> list[str]:
    return [
        "Lag_1",
        "Lag_3",
        "Lag_7",
        "Lag_14",
        "Lag_21",
        "Lag_30",
        "Lag_60",
        "Lag_90",
        "RollingMean_3",
        "RollingMean_7",
        "RollingMean_14",
        "RollingMean_30",
        "RollingStd_7",
        "RollingStd_14",
        "RollingStd_30",
        "RollingMedian",
        "RollingMax",
        "RollingMin",
        "ExpandingMean",
        "ExpandingStd",
        "Day",
        "Week",
        "Month",
        "Quarter",
        "Year",
        "WeekOfYear",
        "DayOfWeek",
        "DayOfMonth",
        "MonthStart",
        "MonthEnd",
        "QuarterStart",
        "QuarterEnd",
        "Weekend",
        "SeasonCode",
        "Holiday",
        "MonthlyRevenue",
        "MonthlyDemand",
        "CountryDemand",
        "CategoryDemand",
        "ProductDemand",
        "AverageOrderValue",
        "BasketSize",
        "CustomerFrequency",
        "ProductFrequency",
        "DailyGrowth",
        "WeeklyGrowth",
        "MonthlyGrowth",
    ]


def feature_descriptions() -> dict[str, str]:
    return {
        "Lag_1": "Prior-day demand is a strong proxy for immediate replenishment pressure.",
        "Lag_3": "Three-day history captures short operational momentum.",
        "Lag_7": "Seven-day demand reflects weekly shopping cadence and promotions.",
        "Lag_14": "Two-week demand stabilizes recent volatility.",
        "Lag_21": "Three-week demand helps identify repeat buying cycles.",
        "Lag_30": "Thirty-day demand anchors monthly seasonality.",
        "Lag_60": "Sixty-day demand captures medium-term trend.",
        "Lag_90": "Ninety-day demand provides quarterly planning context.",
        "RollingMean_3": "Short rolling averages highlight immediate demand shifts.",
        "RollingMean_7": "Weekly rolling averages capture recurring purchase rhythm.",
        "RollingMean_14": "Biweekly averages smooth transient noise.",
        "RollingMean_30": "Monthly rolling averages represent underlying baseline demand.",
        "RollingStd_7": "Seven-day variability shows short-term demand instability.",
        "RollingStd_14": "Two-week variability captures demand turbulence.",
        "RollingStd_30": "Monthly variability helps flag planning risk.",
        "RollingMedian": "Median demand is robust to one-off spikes.",
        "RollingMax": "Recent demand peaks highlight upside capacity needs.",
        "RollingMin": "Recent demand floors show likely downside demand.",
        "ExpandingMean": "Cumulative mean encodes the long-run demand level.",
        "ExpandingStd": "Cumulative volatility reflects series maturity and uncertainty.",
        "Day": "Calendar day can influence pay-cycle and holiday adjacency effects.",
        "Week": "Week number captures recurring retail calendar behavior.",
        "Month": "Month captures seasonality and assortment changes.",
        "Quarter": "Quarter captures broader commercial cycles.",
        "Year": "Year tracks secular demand shifts over time.",
        "WeekOfYear": "Week-of-year captures holiday and seasonal peaks.",
        "DayOfWeek": "Day-of-week reflects weekday versus weekend shopping behavior.",
        "DayOfMonth": "Month-end and payday effects often change demand intensity.",
        "MonthStart": "Month start can align with budget resets and replenishment cadence.",
        "MonthEnd": "Month end often carries promotion and stock-clearance effects.",
        "QuarterStart": "Quarter start can shift planning and ordering patterns.",
        "QuarterEnd": "Quarter end often reflects target-driven activity.",
        "Weekend": "Weekend demand behaves differently from working days.",
        "SeasonCode": "Seasonality captures broad weather and holiday context.",
        "Holiday": "Holiday markers capture exceptional seasonal demand spikes.",
        "MonthlyRevenue": "Trailing monthly revenue reflects current commercial velocity.",
        "MonthlyDemand": "Trailing monthly demand encodes local demand density.",
        "CountryDemand": "Country-level demand captures macro market pull.",
        "CategoryDemand": "Category demand indicates assortment-level momentum.",
        "ProductDemand": "Product-level demand captures cross-market item popularity.",
        "AverageOrderValue": "Order value indicates spending depth per basket.",
        "BasketSize": "Basket size reveals merchandising attachment and bundle behavior.",
        "CustomerFrequency": "Customer frequency captures repeat-shopper activity.",
        "ProductFrequency": "Product frequency shows how persistently the item moves.",
        "DailyGrowth": "Day-over-day growth highlights fresh acceleration or slowdown.",
        "WeeklyGrowth": "Weekly growth captures short trend changes.",
        "MonthlyGrowth": "Monthly growth represents strategic demand direction.",
    }


def normalize_retail_frame(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    rename_map = {
        "Customer ID": "CustomerID",
        "Invoice": "InvoiceNo",
        "Price": "UnitPrice",
        "TotalAmount": "Revenue",
    }
    applicable = {src: dst for src, dst in rename_map.items() if src in data.columns and dst not in data.columns}
    if applicable:
        data = data.rename(columns=applicable)

    required = {"InvoiceDate", "Description", "Country", "Quantity"}
    missing = required.difference(data.columns)
    if missing:
        raise KeyError(f"Input data is missing required columns: {sorted(missing)}")

    if "InvoiceNo" not in data.columns:
        data["InvoiceNo"] = data.index.astype(str)
    if "CustomerID" not in data.columns:
        data["CustomerID"] = -1
    if "ProductCategory" not in data.columns:
        data["ProductCategory"] = data["Description"].apply(classify_product)
    if "Revenue" not in data.columns:
        if "UnitPrice" not in data.columns:
            raise KeyError("Revenue is missing and cannot be derived because UnitPrice is unavailable")
        data["Revenue"] = pd.to_numeric(data["Quantity"], errors="coerce").fillna(0) * pd.to_numeric(
            data["UnitPrice"], errors="coerce"
        ).fillna(0)

    data["InvoiceDate"] = pd.to_datetime(data["InvoiceDate"], errors="coerce")
    data["Quantity"] = pd.to_numeric(data["Quantity"], errors="coerce").fillna(0)
    data["Revenue"] = pd.to_numeric(data["Revenue"], errors="coerce").fillna(0)
    data["Description"] = data["Description"].fillna("Unknown").astype(str)
    data["Country"] = data["Country"].fillna("Unknown").astype(str)
    data["ProductCategory"] = data["ProductCategory"].fillna("Other").astype(str)
    data["CustomerID"] = pd.to_numeric(data["CustomerID"], errors="coerce").fillna(-1).astype(int)
    data = data.dropna(subset=["InvoiceDate"]).copy()
    data = data[data["Quantity"] >= 0].copy()
    return data.reset_index(drop=True)


def build_daily_aggregate(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.Timestamp]:
    normalized = normalize_retail_frame(data)
    normalized["Date"] = normalized["InvoiceDate"].dt.normalize()
    daily = (
        normalized.groupby(["Date", "Description", "Country", "ProductCategory"], as_index=False)
        .agg(
            Sales=("Quantity", "sum"),
            Revenue=("Revenue", "sum"),
            Orders=("InvoiceNo", "nunique"),
            UniqueCustomers=("CustomerID", "nunique"),
        )
        .sort_values(["Description", "Country", "ProductCategory", "Date"])
        .reset_index(drop=True)
    )
    end_date = pd.Timestamp(daily["Date"].max())
    series_meta = (
        daily.groupby(["Description", "Country", "ProductCategory"], as_index=False)
        .agg(
            TotalSales=("Sales", "sum"),
            TotalRevenue=("Revenue", "sum"),
            StartDate=("Date", "min"),
            EndDate=("Date", "max"),
            ActiveDays=("Date", "nunique"),
        )
        .sort_values(["TotalSales", "TotalRevenue", "ActiveDays"], ascending=False)
        .reset_index(drop=True)
    )
    series_meta["AvailableHistoryDays"] = (end_date - pd.to_datetime(series_meta["StartDate"])).dt.days + 1
    series_meta["AvgUnitPrice"] = np.where(
        series_meta["TotalSales"] > 0,
        series_meta["TotalRevenue"] / series_meta["TotalSales"],
        0.0,
    )
    series_meta["SeriesKey"] = (
        series_meta["Description"].astype(str)
        + " | "
        + series_meta["Country"].astype(str)
        + " | "
        + series_meta["ProductCategory"].astype(str)
    )
    return daily, series_meta, end_date


def build_context_tables(daily: pd.DataFrame) -> dict[str, pd.DataFrame]:
    country = (
        daily.groupby(["Country", "Date"], as_index=False)
        .agg(
            CountrySalesRaw=("Sales", "sum"),
            CountryRevenueRaw=("Revenue", "sum"),
            CountryOrdersRaw=("Orders", "sum"),
        )
        .sort_values(["Country", "Date"])
        .reset_index(drop=True)
    )
    category = (
        daily.groupby(["ProductCategory", "Date"], as_index=False)
        .agg(
            CategorySalesRaw=("Sales", "sum"),
            CategoryRevenueRaw=("Revenue", "sum"),
            CategoryOrdersRaw=("Orders", "sum"),
        )
        .sort_values(["ProductCategory", "Date"])
        .reset_index(drop=True)
    )
    product = (
        daily.groupby(["Description", "Date"], as_index=False)
        .agg(
            ProductSalesRaw=("Sales", "sum"),
            ProductRevenueRaw=("Revenue", "sum"),
            ProductOrdersRaw=("Orders", "sum"),
        )
        .sort_values(["Description", "Date"])
        .reset_index(drop=True)
    )
    return {"country": country, "category": category, "product": product}


def select_top_series(series_meta: pd.DataFrame, top_n_series: int, min_history: int) -> pd.DataFrame:
    min_required = max(LAG_WINDOWS) + min_history
    eligible = series_meta[series_meta["AvailableHistoryDays"] >= min_required].copy()
    if eligible.empty:
        logger.warning("No series met the full history threshold. Falling back to highest-volume series.")
        eligible = series_meta.copy()
    return (
        eligible.sort_values(["TotalSales", "TotalRevenue", "ActiveDays"], ascending=False)
        .head(max(1, top_n_series))
        .reset_index(drop=True)
    )


def add_engineered_features(series_df: pd.DataFrame) -> pd.DataFrame:
    series = series_df.sort_values("Date").copy()
    shifted_sales = series["Sales"].shift(1)
    shifted_revenue = series["Revenue"].shift(1)
    shifted_orders = series["Orders"].shift(1)
    shifted_customers = series["UniqueCustomers"].shift(1)
    rolling_orders = shifted_orders.rolling(window=30, min_periods=1).sum()
    rolling_orders_safe = rolling_orders.replace(0, np.nan)
    rolling_sales_30 = shifted_sales.rolling(window=30, min_periods=1).sum()

    series["Day"] = series["Date"].dt.day
    series["DayOfMonth"] = series["Date"].dt.day
    series["Week"] = series["Date"].dt.isocalendar().week.astype(int)
    series["WeekOfYear"] = series["Date"].dt.isocalendar().week.astype(int)
    series["Month"] = series["Date"].dt.month.astype(int)
    series["Quarter"] = series["Date"].dt.quarter.astype(int)
    series["Year"] = series["Date"].dt.year.astype(int)
    series["DayOfWeek"] = series["Date"].dt.dayofweek.astype(int)
    series["MonthStart"] = series["Date"].dt.is_month_start.astype(int)
    series["MonthEnd"] = series["Date"].dt.is_month_end.astype(int)
    series["QuarterStart"] = series["Date"].dt.is_quarter_start.astype(int)
    series["QuarterEnd"] = series["Date"].dt.is_quarter_end.astype(int)
    series["Weekend"] = series["DayOfWeek"].isin([5, 6]).astype(int)
    series["Season"] = series["Month"].map(SEASON_MAP)
    series["SeasonCode"] = series["Season"].map(SEASON_CODE).astype(int)
    series["Holiday"] = build_holiday_flag(series["Date"])

    for lag in LAG_WINDOWS:
        series[f"Lag_{lag}"] = series["Sales"].shift(lag)
    for window in ROLLING_MEAN_WINDOWS:
        series[f"RollingMean_{window}"] = shifted_sales.rolling(window=window, min_periods=1).mean().fillna(0)
    for window in ROLLING_STD_WINDOWS:
        series[f"RollingStd_{window}"] = shifted_sales.rolling(window=window, min_periods=1).std().fillna(0)

    series["RollingMedian"] = shifted_sales.rolling(window=30, min_periods=1).median().fillna(0)
    series["RollingMax"] = shifted_sales.rolling(window=30, min_periods=1).max().fillna(0)
    series["RollingMin"] = shifted_sales.rolling(window=30, min_periods=1).min().fillna(0)
    series["ExpandingMean"] = shifted_sales.expanding(min_periods=1).mean().fillna(0)
    series["ExpandingStd"] = shifted_sales.expanding(min_periods=2).std().fillna(0)

    series["MonthlyRevenue"] = shifted_revenue.rolling(window=30, min_periods=1).sum().fillna(0)
    series["MonthlyDemand"] = rolling_sales_30.fillna(0)
    series["CountryDemand"] = (
        series["CountrySalesRaw"].shift(1).rolling(window=30, min_periods=1).sum().fillna(0)
    )
    series["CategoryDemand"] = (
        series["CategorySalesRaw"].shift(1).rolling(window=30, min_periods=1).sum().fillna(0)
    )
    series["ProductDemand"] = (
        series["ProductSalesRaw"].shift(1).rolling(window=30, min_periods=1).sum().fillna(0)
    )
    series["AverageOrderValue"] = (series["MonthlyRevenue"] / rolling_orders_safe).replace(
        [np.inf, -np.inf], np.nan
    ).fillna(0)
    series["BasketSize"] = (rolling_sales_30 / rolling_orders_safe).replace([np.inf, -np.inf], np.nan).fillna(0)
    series["CustomerFrequency"] = shifted_customers.rolling(window=30, min_periods=1).mean().fillna(0)
    series["ProductFrequency"] = (
        series["ProductOrdersRaw"].shift(1).rolling(window=30, min_periods=1).sum().fillna(0)
    )

    weekly_base = shifted_sales.rolling(window=7, min_periods=1).mean()
    monthly_base = shifted_sales.rolling(window=30, min_periods=1).mean()
    series["DailyGrowth"] = shifted_sales.pct_change().replace([np.inf, -np.inf], 0).fillna(0)
    series["WeeklyGrowth"] = weekly_base.pct_change().replace([np.inf, -np.inf], 0).fillna(0)
    series["MonthlyGrowth"] = monthly_base.pct_change().replace([np.inf, -np.inf], 0).fillna(0)
    series["Target"] = series["Sales"].astype(float)
    return series


def prepare_feature_dataset(
    data: pd.DataFrame,
    top_n_series: int = DEFAULT_TOP_N_SERIES,
    min_history: int = DEFAULT_MIN_HISTORY,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, pd.DataFrame]]:
    logger.info("Building enterprise forecasting feature dataset")
    daily, series_meta, end_date = build_daily_aggregate(data)
    selected_meta = select_top_series(series_meta, top_n_series=top_n_series, min_history=min_history)
    contexts = build_context_tables(daily)
    selected_frames: dict[str, pd.DataFrame] = {}
    prepared_frames: list[pd.DataFrame] = []

    for row in selected_meta.itertuples(index=False):
        mask = (
            (daily["Description"] == row.Description)
            & (daily["Country"] == row.Country)
            & (daily["ProductCategory"] == row.ProductCategory)
        )
        sparse = daily.loc[mask].copy()
        if sparse.empty:
            continue

        index = pd.date_range(pd.Timestamp(sparse["Date"].min()), end_date, freq="D")
        completed = pd.DataFrame({"Date": index})
        completed = completed.merge(sparse, on="Date", how="left")
        completed["Description"] = completed["Description"].fillna(row.Description)
        completed["Country"] = completed["Country"].fillna(row.Country)
        completed["ProductCategory"] = completed["ProductCategory"].fillna(row.ProductCategory)
        for numeric in ["Sales", "Revenue", "Orders", "UniqueCustomers"]:
            completed[numeric] = pd.to_numeric(completed[numeric], errors="coerce").fillna(0.0)

        completed = completed.merge(contexts["country"], on=["Country", "Date"], how="left")
        completed = completed.merge(contexts["category"], on=["ProductCategory", "Date"], how="left")
        completed = completed.merge(contexts["product"], on=["Description", "Date"], how="left")

        for column in [
            "CountrySalesRaw",
            "CountryRevenueRaw",
            "CountryOrdersRaw",
            "CategorySalesRaw",
            "CategoryRevenueRaw",
            "CategoryOrdersRaw",
            "ProductSalesRaw",
            "ProductRevenueRaw",
            "ProductOrdersRaw",
        ]:
            completed[column] = pd.to_numeric(completed[column], errors="coerce").fillna(0.0)

        completed["SeriesKey"] = row.SeriesKey
        completed["AvgUnitPriceSeries"] = float(row.AvgUnitPrice) if pd.notna(row.AvgUnitPrice) else 0.0
        completed = add_engineered_features(completed)
        selected_frames[row.SeriesKey] = completed.copy()

        trainable = completed.dropna(
            subset=[f"Lag_{lag}" for lag in LAG_WINDOWS]
        ).reset_index(drop=True)
        if len(trainable) < min_history:
            logger.info("Skipping %s because trainable history is %s rows", row.SeriesKey, len(trainable))
            continue
        prepared_frames.append(trainable)

    if not prepared_frames:
        raise ValueError("No forecastable time series met the minimum history requirement.")

    prepared = pd.concat(prepared_frames, ignore_index=True)
    prepared = prepared.sort_values(["SeriesKey", "Date"]).reset_index(drop=True)
    valid_keys = set(prepared["SeriesKey"].unique().tolist())
    filtered_meta = selected_meta[selected_meta["SeriesKey"].isin(valid_keys)].reset_index(drop=True)
    return prepared, filtered_meta, daily, selected_frames


def clean_feature_matrix(frame: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
    cleaned = frame.loc[:, list(columns)].copy()
    for column in cleaned.columns:
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")
    return cleaned.fillna(0)


def resolve_time_series_splitter(
    n_rows: int,
    test_size: int = DEFAULT_TEST_SIZE,
    min_train_size: int = DEFAULT_MIN_HISTORY,
    desired_splits: int = 3,
) -> TimeSeriesSplit | None:
    possible_splits = (n_rows - min_train_size) // test_size
    if possible_splits < 2:
        return None
    return TimeSeriesSplit(n_splits=min(desired_splits, possible_splits), test_size=test_size)


def sklearn_pipeline(regressor: Any, scale: bool = False) -> Pipeline:
    steps: list[tuple[str, Any]] = [("imputer", SimpleImputer(strategy="median"))]
    if scale:
        steps.append(("scaler", StandardScaler()))
    steps.append(("regressor", regressor))
    return Pipeline(steps)


def model_catalog() -> dict[str, ModelSpec]:
    catalog = {
        "Naive": ModelSpec(name="Naive", family="baseline", available=True),
        "Seasonal Naive": ModelSpec(name="Seasonal Naive", family="baseline", available=True),
        "Moving Average": ModelSpec(name="Moving Average", family="baseline", available=True),
        "Exponential Smoothing": ModelSpec(
            name="Exponential Smoothing",
            family="statistical",
            available=StatsExponentialSmoothing is not None,
            reason_unavailable="statsmodels is not installed",
        ),
        "Holt": ModelSpec(
            name="Holt",
            family="statistical",
            available=StatsHolt is not None,
            reason_unavailable="statsmodels is not installed",
        ),
        "Holt-Winters": ModelSpec(
            name="Holt-Winters",
            family="statistical",
            available=StatsExponentialSmoothing is not None,
            reason_unavailable="statsmodels is not installed",
        ),
        "ARIMA": ModelSpec(
            name="ARIMA",
            family="statistical",
            available=StatsARIMA is not None,
            reason_unavailable="statsmodels is not installed",
        ),
        "SARIMA": ModelSpec(
            name="SARIMA",
            family="statistical",
            available=StatsARIMA is not None,
            reason_unavailable="statsmodels is not installed",
        ),
        "Linear Regression": ModelSpec(
            name="Linear Regression",
            family="machine_learning",
            available=True,
            factory=lambda params=None: sklearn_pipeline(LinearRegression(**(params or {})), scale=True),
        ),
        "Ridge": ModelSpec(
            name="Ridge",
            family="machine_learning",
            available=True,
            factory=lambda params=None: sklearn_pipeline(Ridge(**({"alpha": 1.0} | (params or {}))), scale=True),
            search_strategy="grid",
            param_grid={"regressor__alpha": [0.1, 1.0, 5.0, 10.0]},
        ),
        "Lasso": ModelSpec(
            name="Lasso",
            family="machine_learning",
            available=True,
            factory=lambda params=None: sklearn_pipeline(
                Lasso(max_iter=5000, **({"alpha": 0.001} | (params or {}))),
                scale=True,
            ),
            search_strategy="grid",
            param_grid={"regressor__alpha": [0.0005, 0.001, 0.01, 0.05]},
        ),
        "ElasticNet": ModelSpec(
            name="ElasticNet",
            family="machine_learning",
            available=True,
            factory=lambda params=None: sklearn_pipeline(
                ElasticNet(
                    max_iter=5000,
                    **({"alpha": 0.01, "l1_ratio": 0.5} | (params or {})),
                ),
                scale=True,
            ),
            search_strategy="grid",
            param_grid={
                "regressor__alpha": [0.001, 0.01, 0.1],
                "regressor__l1_ratio": [0.2, 0.5, 0.8],
            },
        ),
        "Decision Tree": ModelSpec(
            name="Decision Tree",
            family="machine_learning",
            available=True,
            factory=lambda params=None: sklearn_pipeline(
                DecisionTreeRegressor(random_state=42, **({"max_depth": 6, "min_samples_leaf": 2} | (params or {})))
            ),
            search_strategy="grid",
            param_grid={
                "regressor__max_depth": [4, 6, 8, 10],
                "regressor__min_samples_leaf": [1, 2, 4],
            },
        ),
        "Random Forest": ModelSpec(
            name="Random Forest",
            family="machine_learning",
            available=True,
            factory=lambda params=None: sklearn_pipeline(
                RandomForestRegressor(
                    n_estimators=250,
                    random_state=42,
                    n_jobs=-1,
                    **({"max_depth": None, "min_samples_leaf": 2} | (params or {})),
                )
            ),
            search_strategy="random",
            param_grid={
                "regressor__n_estimators": [150, 250, 400],
                "regressor__max_depth": [None, 8, 12],
                "regressor__min_samples_leaf": [1, 2, 4],
                "regressor__max_features": ["sqrt", 0.6, None],
            },
        ),
        "Extra Trees": ModelSpec(
            name="Extra Trees",
            family="machine_learning",
            available=True,
            factory=lambda params=None: sklearn_pipeline(
                ExtraTreesRegressor(
                    n_estimators=300,
                    random_state=42,
                    n_jobs=-1,
                    **({"max_depth": None, "min_samples_leaf": 1} | (params or {})),
                )
            ),
            search_strategy="random",
            param_grid={
                "regressor__n_estimators": [150, 300, 450],
                "regressor__max_depth": [None, 8, 12],
                "regressor__min_samples_leaf": [1, 2, 4],
                "regressor__max_features": ["sqrt", 0.6, None],
            },
        ),
        "Gradient Boosting": ModelSpec(
            name="Gradient Boosting",
            family="machine_learning",
            available=True,
            factory=lambda params=None: sklearn_pipeline(
                GradientBoostingRegressor(
                    random_state=42,
                    n_iter_no_change=5,
                    validation_fraction=0.1,
                    **({"n_estimators": 200, "learning_rate": 0.05, "max_depth": 3} | (params or {})),
                )
            ),
            search_strategy="random",
            param_grid={
                "regressor__n_estimators": [120, 200, 300],
                "regressor__learning_rate": [0.03, 0.05, 0.1],
                "regressor__max_depth": [2, 3, 4],
            },
        ),
        "AdaBoost": ModelSpec(
            name="AdaBoost",
            family="machine_learning",
            available=True,
            factory=lambda params=None: sklearn_pipeline(
                AdaBoostRegressor(
                    random_state=42,
                    **({"n_estimators": 200, "learning_rate": 0.05} | (params or {})),
                )
            ),
            search_strategy="grid",
            param_grid={
                "regressor__n_estimators": [100, 200, 300],
                "regressor__learning_rate": [0.03, 0.05, 0.1],
            },
        ),
        "MLP": ModelSpec(
            name="MLP",
            family="machine_learning",
            available=True,
            factory=lambda params=None: sklearn_pipeline(
                MLPRegressor(
                    random_state=42,
                    max_iter=400,
                    early_stopping=True,
                    validation_fraction=0.15,
                    **(
                        {
                            "hidden_layer_sizes": (64, 32),
                            "alpha": 0.0005,
                            "learning_rate_init": 0.001,
                        }
                        | (params or {})
                    ),
                ),
                scale=True,
            ),
            search_strategy="random",
            param_grid={
                "regressor__hidden_layer_sizes": [(32,), (64, 32), (128, 64)],
                "regressor__alpha": [0.0001, 0.0005, 0.001],
                "regressor__learning_rate_init": [0.0005, 0.001, 0.005],
            },
        ),
        "XGBoost": ModelSpec(
            name="XGBoost",
            family="machine_learning",
            available=XGBRegressor is not None,
            factory=(
                lambda params=None: sklearn_pipeline(
                    XGBRegressor(
                        random_state=42,
                        n_estimators=250,
                        learning_rate=0.05,
                        max_depth=5,
                        n_jobs=-1,
                        verbosity=0,
                        **(params or {}),
                    )
                )
            )
            if XGBRegressor is not None
            else None,
            reason_unavailable="xgboost is not installed",
            search_strategy="random",
            param_grid={
                "regressor__n_estimators": [150, 250, 400],
                "regressor__learning_rate": [0.03, 0.05, 0.1],
                "regressor__max_depth": [3, 5, 7],
                "regressor__subsample": [0.7, 0.9, 1.0],
            },
        ),
        "LightGBM": ModelSpec(
            name="LightGBM",
            family="machine_learning",
            available=LGBMRegressor is not None,
            factory=(
                lambda params=None: sklearn_pipeline(
                    LGBMRegressor(
                        random_state=42,
                        n_estimators=250,
                        learning_rate=0.05,
                        **(params or {}),
                    )
                )
            )
            if LGBMRegressor is not None
            else None,
            reason_unavailable="lightgbm is not installed",
            search_strategy="random",
            param_grid={
                "regressor__n_estimators": [150, 250, 400],
                "regressor__learning_rate": [0.03, 0.05, 0.1],
                "regressor__num_leaves": [31, 63, 127],
            },
        ),
        "CatBoost": ModelSpec(
            name="CatBoost",
            family="machine_learning",
            available=CatBoostRegressor is not None,
            factory=(
                lambda params=None: sklearn_pipeline(
                    CatBoostRegressor(
                        verbose=False,
                        random_seed=42,
                        iterations=250,
                        learning_rate=0.05,
                        depth=6,
                        **(params or {}),
                    )
                )
            )
            if CatBoostRegressor is not None
            else None,
            reason_unavailable="catboost is not installed",
            search_strategy="random",
            param_grid={
                "regressor__iterations": [150, 250, 400],
                "regressor__learning_rate": [0.03, 0.05, 0.1],
                "regressor__depth": [4, 6, 8],
            },
        ),
        "Prophet": ModelSpec(
            name="Prophet",
            family="time_series_library",
            available=Prophet is not None,
            reason_unavailable="prophet is not installed",
        ),
        "AutoARIMA": ModelSpec(
            name="AutoARIMA",
            family="time_series_library",
            available=auto_arima is not None,
            reason_unavailable="pmdarima is not installed",
        ),
        "LSTM": ModelSpec(
            name="LSTM",
            family="deep_learning",
            available=tf is not None,
            reason_unavailable="tensorflow is not installed",
        ),
        "Bidirectional LSTM": ModelSpec(
            name="Bidirectional LSTM",
            family="deep_learning",
            available=tf is not None,
            reason_unavailable="tensorflow is not installed",
        ),
        "GRU": ModelSpec(
            name="GRU",
            family="deep_learning",
            available=tf is not None,
            reason_unavailable="tensorflow is not installed",
        ),
        "CNN-LSTM": ModelSpec(
            name="CNN-LSTM",
            family="deep_learning",
            available=tf is not None,
            reason_unavailable="tensorflow is not installed",
        ),
    }
    return catalog


def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": rmse_metric(y_true, y_pred),
        "mape": safe_mape(y_true, y_pred),
        "smape": safe_smape(y_true, y_pred),
        "r2": float(r2_score(y_true, y_pred)),
        "mase": mean_absolute_scaled_error(y_true, y_pred),
    }


def predict_baseline(model_name: str, history: Sequence[float], horizon: int) -> np.ndarray:
    series = [float(value) for value in history]
    if not series:
        return np.zeros(horizon, dtype=float)
    predictions: list[float] = []
    seasonality = 7

    for step in range(horizon):
        if model_name == "Naive":
            pred = float(series[-1])
        elif model_name == "Seasonal Naive":
            if len(series) >= seasonality:
                pred = float(series[-seasonality])
            else:
                pred = float(series[-1])
        else:
            window = min(seasonality, len(series))
            pred = float(np.mean(series[-window:]))
        predictions.append(max(0.0, pred))
        series.append(max(0.0, pred))
    return np.asarray(predictions, dtype=float)


def fit_model(
    model_name: str,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    train_dates: pd.Series,
    selected_features: Sequence[str],
    params: dict[str, Any] | None = None,
) -> FittedModelBundle:
    specs = model_catalog()
    spec = specs[model_name]
    chosen_features = list(selected_features)
    params = params or {}

    if model_name in {"Naive", "Seasonal Naive", "Moving Average"}:
        return FittedModelBundle(
            model_name=model_name,
            kind="baseline",
            estimator=None,
            feature_columns=list(X_train.columns),
            selected_features=chosen_features,
            params=params,
            metadata={"history": y_train.astype(float).tolist()},
        )

    if model_name == "Exponential Smoothing":
        estimator = StatsExponentialSmoothing(
            y_train,
            trend=None,
            seasonal=None,
            initialization_method="estimated",
        ).fit(optimized=True)
        return FittedModelBundle(model_name, "statsmodels", estimator, list(X_train.columns), chosen_features, params)
    if model_name == "Holt":
        estimator = StatsHolt(y_train).fit(optimized=True)
        return FittedModelBundle(model_name, "statsmodels", estimator, list(X_train.columns), chosen_features, params)
    if model_name == "Holt-Winters":
        estimator = StatsExponentialSmoothing(
            y_train,
            trend="add",
            seasonal="add",
            seasonal_periods=7,
            initialization_method="estimated",
        ).fit(optimized=True)
        return FittedModelBundle(model_name, "statsmodels", estimator, list(X_train.columns), chosen_features, params)
    if model_name == "ARIMA":
        estimator = StatsARIMA(y_train, order=(1, 1, 1)).fit()
        return FittedModelBundle(model_name, "statsmodels", estimator, list(X_train.columns), chosen_features, params)
    if model_name == "SARIMA":
        estimator = StatsARIMA(y_train, order=(1, 1, 1), seasonal_order=(1, 0, 1, 7)).fit()
        return FittedModelBundle(model_name, "statsmodels", estimator, list(X_train.columns), chosen_features, params)
    if model_name == "Prophet":
        prophet_frame = pd.DataFrame({"ds": pd.to_datetime(train_dates), "y": y_train.astype(float).to_numpy()})
        estimator = Prophet()
        estimator.fit(prophet_frame)
        return FittedModelBundle(model_name, "prophet", estimator, list(X_train.columns), chosen_features, params)
    if model_name == "AutoARIMA":
        estimator = auto_arima(y_train.astype(float).to_numpy(), seasonal=True, m=7, suppress_warnings=True)
        return FittedModelBundle(model_name, "autoarima", estimator, list(X_train.columns), chosen_features, params)

    if spec.factory is None:
        raise ValueError(f"No factory configured for model {model_name}")

    estimator = spec.factory(params)
    estimator.fit(X_train.loc[:, chosen_features], y_train.astype(float))
    return FittedModelBundle(
        model_name=model_name,
        kind="supervised",
        estimator=estimator,
        feature_columns=list(X_train.columns),
        selected_features=chosen_features,
        params=params,
    )


def predict_with_bundle(
    bundle: FittedModelBundle,
    X_frame: pd.DataFrame,
    future_dates: Sequence[pd.Timestamp],
    history: Sequence[float],
) -> np.ndarray:
    horizon = len(future_dates)
    if bundle.kind == "baseline":
        return predict_baseline(bundle.model_name, history, horizon)
    if bundle.kind == "statsmodels":
        return np.asarray(bundle.estimator.forecast(horizon), dtype=float)
    if bundle.kind == "prophet":
        future = pd.DataFrame({"ds": pd.to_datetime(list(future_dates))})
        prediction = bundle.estimator.predict(future)
        return prediction["yhat"].to_numpy(dtype=float)
    if bundle.kind == "autoarima":
        return np.asarray(bundle.estimator.predict(n_periods=horizon), dtype=float)
    return np.asarray(bundle.estimator.predict(X_frame.loc[:, bundle.selected_features]), dtype=float)


def evaluate_model_on_series(
    series_df: pd.DataFrame,
    model_name: str,
    config_label: str,
    selected_features: Sequence[str],
    params: dict[str, Any] | None = None,
    test_size: int = DEFAULT_TEST_SIZE,
    collect_predictions: bool = False,
) -> tuple[dict[str, Any], pd.DataFrame]:
    features = clean_feature_matrix(series_df, feature_columns())
    target = pd.to_numeric(series_df["Target"], errors="coerce").fillna(0).astype(float)
    dates = pd.to_datetime(series_df["Date"])
    splitter = resolve_time_series_splitter(len(series_df), test_size=test_size)

    if splitter is None:
        return (
            {
                "model_name": model_name,
                "configuration": config_label,
                "series_key": series_df["SeriesKey"].iloc[0],
                "status": "insufficient_history",
                "reason": "Not enough rows for rolling-origin validation.",
                "mae": np.nan,
                "rmse": np.nan,
                "mape": np.nan,
                "smape": np.nan,
                "r2": np.nan,
                "mase": np.nan,
            },
            pd.DataFrame(),
        )

    fold_metrics: list[dict[str, float]] = []
    prediction_rows: list[pd.DataFrame] = []
    valid_folds = 0

    for fold_id, (train_idx, test_idx) in enumerate(splitter.split(features), start=1):
        X_train = features.iloc[train_idx].reset_index(drop=True)
        X_test = features.iloc[test_idx].reset_index(drop=True)
        y_train = target.iloc[train_idx].reset_index(drop=True)
        y_test = target.iloc[test_idx].reset_index(drop=True)
        date_train = dates.iloc[train_idx].reset_index(drop=True)
        date_test = dates.iloc[test_idx].reset_index(drop=True)

        try:
            bundle = fit_model(
                model_name=model_name,
                X_train=X_train,
                y_train=y_train,
                train_dates=date_train,
                selected_features=selected_features,
                params=params,
            )
            preds = predict_with_bundle(
                bundle=bundle,
                X_frame=X_test,
                future_dates=date_test.tolist(),
                history=y_train.tolist(),
            )
            preds = np.clip(np.asarray(preds, dtype=float), a_min=0.0, a_max=None)
            metrics = evaluate_predictions(y_test.to_numpy(dtype=float), preds)
            fold_metrics.append(metrics)
            valid_folds += 1

            if collect_predictions:
                frame = pd.DataFrame(
                    {
                        "Date": date_test,
                        "SeriesKey": series_df["SeriesKey"].iloc[0],
                        "Product": series_df["Description"].iloc[0],
                        "Country": series_df["Country"].iloc[0],
                        "ProductCategory": series_df["ProductCategory"].iloc[0],
                        "Fold": fold_id,
                        "Model": model_name,
                        "Configuration": config_label,
                        "Actual": y_test.to_numpy(dtype=float),
                        "Forecast": preds,
                    }
                )
                frame["Residual"] = frame["Actual"] - frame["Forecast"]
                prediction_rows.append(frame)
        except Exception as exc:
            logger.warning("Model %s failed on %s fold %s: %s", model_name, series_df["SeriesKey"].iloc[0], fold_id, exc)

    if valid_folds == 0:
        return (
            {
                "model_name": model_name,
                "configuration": config_label,
                "series_key": series_df["SeriesKey"].iloc[0],
                "status": "failed",
                "reason": "Every rolling fold failed.",
                "mae": np.nan,
                "rmse": np.nan,
                "mape": np.nan,
                "smape": np.nan,
                "r2": np.nan,
                "mase": np.nan,
            },
            pd.DataFrame(),
        )

    summary = {
        "model_name": model_name,
        "configuration": config_label,
        "series_key": series_df["SeriesKey"].iloc[0],
        "status": "evaluated",
        "reason": "",
        "mae": float(np.mean([item["mae"] for item in fold_metrics])),
        "rmse": float(np.mean([item["rmse"] for item in fold_metrics])),
        "mape": float(np.mean([item["mape"] for item in fold_metrics])),
        "smape": float(np.mean([item["smape"] for item in fold_metrics])),
        "r2": float(np.mean([item["r2"] for item in fold_metrics])),
        "mase": float(np.mean([item["mase"] for item in fold_metrics])),
    }
    predictions = pd.concat(prediction_rows, ignore_index=True) if prediction_rows else pd.DataFrame()
    return summary, predictions


def unavailable_model_rows() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for spec in model_catalog().values():
        if spec.available:
            continue
        rows.append(
            {
                "model_name": spec.name,
                "configuration": "default",
                "series_key": "ALL",
                "status": "unavailable",
                "reason": spec.reason_unavailable or "Optional dependency is unavailable.",
                "mae": np.nan,
                "rmse": np.nan,
                "mape": np.nan,
                "smape": np.nan,
                "r2": np.nan,
                "mase": np.nan,
            }
        )
    return pd.DataFrame(rows)


def aggregate_leaderboard(metrics_df: pd.DataFrame) -> pd.DataFrame:
    evaluated = metrics_df[metrics_df["status"] == "evaluated"].copy()
    if evaluated.empty:
        return pd.DataFrame(
            columns=[
                "model_name",
                "configuration",
                "series_count",
                "selection_eligible",
                "mae",
                "rmse",
                "mape",
                "smape",
                "r2",
                "mase",
            ]
        )
    leaderboard = (
        evaluated.groupby(["model_name", "configuration"], as_index=False)
        .agg(
            series_count=("series_key", "nunique"),
            mae=("mae", "mean"),
            rmse=("rmse", "mean"),
            mape=("mape", "mean"),
            smape=("smape", "mean"),
            r2=("r2", "mean"),
            mase=("mase", "mean"),
        )
    )
    max_coverage = int(leaderboard["series_count"].max()) if not leaderboard.empty else 0
    leaderboard["selection_eligible"] = leaderboard["series_count"].eq(max_coverage)
    leaderboard = leaderboard.sort_values(["rmse", "mae", "mape"], ascending=True).reset_index(drop=True)
    return leaderboard


def select_best_model(leaderboard: pd.DataFrame) -> dict[str, Any]:
    if leaderboard.empty:
        return {
            "model_name": "Naive",
            "configuration": "default",
            "reason": "No candidate model produced a valid rolling-origin score.",
            "params": {},
        }

    eligible = leaderboard[leaderboard["selection_eligible"]].copy()
    pool = eligible if not eligible.empty else leaderboard
    best = pool.iloc[0]
    naive = leaderboard[
        (leaderboard["model_name"] == "Naive") & (leaderboard["configuration"] == "default")
    ]
    excluded_message = ""
    if eligible.shape[0] != leaderboard.shape[0]:
        excluded_count = int((~leaderboard["selection_eligible"]).sum())
        excluded_message = (
            f" {excluded_count} lower-coverage model(s) were kept in the leaderboard but excluded from auto-selection "
            "because they were not evaluated across the full selected-series portfolio."
        )
    if naive.empty or pd.isna(naive.iloc[0]["rmse"]):
        reason = (
            f"{best['model_name']} ({best['configuration']}) delivered the lowest RMSE "
            f"at {best['rmse']:.2f} with MAE {best['mae']:.2f}.{excluded_message}"
        )
    else:
        baseline_rmse = float(naive.iloc[0]["rmse"])
        improvement = 0.0 if baseline_rmse == 0 else (baseline_rmse - float(best["rmse"])) / baseline_rmse * 100.0
        reason = (
            f"{best['model_name']} ({best['configuration']}) won because it produced the lowest RMSE "
            f"({best['rmse']:.2f}) and improved on the Naive baseline by {improvement:.1f}%.{excluded_message}"
        )
    return {
        "model_name": str(best["model_name"]),
        "configuration": str(best["configuration"]),
        "reason": reason,
        "params": {},
    }


def perform_rfe(anchor_series: pd.DataFrame) -> tuple[list[str], pd.DataFrame]:
    columns = feature_columns()
    X = clean_feature_matrix(anchor_series, columns)
    y = pd.to_numeric(anchor_series["Target"], errors="coerce").fillna(0).astype(float)
    estimator = RandomForestRegressor(n_estimators=150, random_state=42, n_jobs=-1)
    selector = RFE(estimator=estimator, n_features_to_select=min(MAX_FEATURE_COUNT, len(columns)))
    selector.fit(X, y)
    ranking = pd.DataFrame({"feature": columns, "ranking": selector.ranking_, "selected": selector.support_})
    ranking = ranking.sort_values(["ranking", "feature"]).reset_index(drop=True)
    selected = ranking[ranking["selected"]]["feature"].tolist()
    return selected, ranking


def tuning_candidate_names(leaderboard: pd.DataFrame) -> list[str]:
    tunable = {
        name
        for name, spec in model_catalog().items()
        if spec.available and spec.factory is not None and spec.search_strategy is not None
    }
    ranked = leaderboard[leaderboard["model_name"].isin(tunable)].copy()
    if ranked.empty:
        return []
    return ranked["model_name"].drop_duplicates().head(3).tolist()


def parameter_space_size(param_grid: dict[str, Sequence[Any]]) -> int:
    size = 1
    for values in param_grid.values():
        size *= max(1, len(values))
    return size


def tune_models(
    anchor_series: pd.DataFrame,
    candidate_names: Sequence[str],
) -> tuple[pd.DataFrame, list[str], pd.DataFrame, dict[str, dict[str, Any]]]:
    if not candidate_names:
        return pd.DataFrame(), feature_columns(), pd.DataFrame(), {}

    splitter = resolve_time_series_splitter(len(anchor_series), test_size=DEFAULT_TEST_SIZE)
    if splitter is None:
        return pd.DataFrame(), feature_columns(), pd.DataFrame(), {}

    selected_features, rfe_ranking = perform_rfe(anchor_series)
    columns = selected_features if selected_features else feature_columns()
    X = clean_feature_matrix(anchor_series, columns)
    y = pd.to_numeric(anchor_series["Target"], errors="coerce").fillna(0).astype(float)
    scorer = make_scorer(rmse_metric, greater_is_better=False)
    rows: list[dict[str, Any]] = []
    params_by_model: dict[str, dict[str, Any]] = {}
    specs = model_catalog()

    for model_name in candidate_names:
        spec = specs[model_name]
        if spec.factory is None or not spec.param_grid:
            continue
        estimator = spec.factory(None)
        try:
            if spec.search_strategy == "random":
                search = RandomizedSearchCV(
                    estimator=estimator,
                    param_distributions=spec.param_grid,
                    n_iter=min(8, parameter_space_size(spec.param_grid)),
                    scoring=scorer,
                    cv=splitter,
                    random_state=42,
                    n_jobs=-1,
                )
            else:
                search = GridSearchCV(
                    estimator=estimator,
                    param_grid=spec.param_grid,
                    scoring=scorer,
                    cv=splitter,
                    n_jobs=-1,
                )
            search.fit(X, y)
            best_params = {key.replace("regressor__", ""): value for key, value in search.best_params_.items()}
            params_by_model[model_name] = best_params
            rows.append(
                {
                    "model_name": model_name,
                    "search_strategy": spec.search_strategy,
                    "selected_feature_count": len(columns),
                    "best_rmse": float(-search.best_score_),
                    "best_params": json_dumps_safe(best_params),
                }
            )
        except Exception as exc:
            logger.warning("Hyperparameter tuning failed for %s: %s", model_name, exc)

    tuning_df = pd.DataFrame(rows).sort_values("best_rmse", ascending=True).reset_index(drop=True) if rows else pd.DataFrame()
    return tuning_df, columns, rfe_ranking, params_by_model


def evaluate_model_set(
    prepared_df: pd.DataFrame,
    model_names: Sequence[str],
    configuration: str,
    selected_features: Sequence[str],
    params_by_model: dict[str, dict[str, Any]] | None = None,
    collect_best_predictions_for: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    metrics_rows: list[dict[str, Any]] = []
    prediction_frames: list[pd.DataFrame] = []
    params_by_model = params_by_model or {}

    for series_key, group in prepared_df.groupby("SeriesKey", sort=False):
        _ = series_key
        for model_name in model_names:
            metrics, predictions = evaluate_model_on_series(
                series_df=group,
                model_name=model_name,
                config_label=configuration,
                selected_features=selected_features,
                params=params_by_model.get(model_name),
                collect_predictions=collect_best_predictions_for == model_name,
            )
            metrics["parameters"] = json_dumps_safe(params_by_model.get(model_name, {}))
            metrics_rows.append(metrics)
            if not predictions.empty:
                prediction_frames.append(predictions)

    metrics_df = pd.DataFrame(metrics_rows)
    predictions_df = pd.concat(prediction_frames, ignore_index=True) if prediction_frames else pd.DataFrame()
    return metrics_df, predictions_df


def build_feature_row_from_history(
    history: pd.DataFrame,
    future_date: pd.Timestamp,
    context: dict[str, float],
) -> dict[str, Any]:
    sales_history = history["Sales"].astype(float)
    revenue_history = history["Revenue"].astype(float)
    orders_history = history["Orders"].astype(float)
    customer_history = history["UniqueCustomers"].astype(float)

    def lag_value(offset: int) -> float:
        if len(sales_history) >= offset:
            return float(sales_history.iloc[-offset])
        return float(sales_history.iloc[-1]) if len(sales_history) else 0.0

    def trailing_mean(window: int) -> float:
        tail = sales_history.tail(window)
        return float(tail.mean()) if not tail.empty else 0.0

    def trailing_std(window: int) -> float:
        tail = sales_history.tail(window)
        return float(tail.std(ddof=0)) if not tail.empty else 0.0

    trailing_orders = float(orders_history.tail(30).sum())
    monthly_revenue = float(revenue_history.tail(30).sum())
    monthly_demand = float(sales_history.tail(30).sum())
    rolling_week = trailing_mean(7)
    previous_week = float(sales_history.tail(14).head(7).mean()) if len(sales_history) >= 14 else rolling_week
    rolling_month = trailing_mean(30)
    previous_month = float(sales_history.tail(60).head(30).mean()) if len(sales_history) >= 60 else rolling_month

    last_value = lag_value(1)
    prior_value = lag_value(2)
    season_name = SEASON_MAP.get(int(future_date.month), "Winter")
    average_order_value = monthly_revenue / trailing_orders if trailing_orders > 0 else context.get("AverageOrderValue", 0.0)
    basket_size = monthly_demand / trailing_orders if trailing_orders > 0 else context.get("BasketSize", 0.0)

    return {
        "Lag_1": lag_value(1),
        "Lag_3": lag_value(3),
        "Lag_7": lag_value(7),
        "Lag_14": lag_value(14),
        "Lag_21": lag_value(21),
        "Lag_30": lag_value(30),
        "Lag_60": lag_value(60),
        "Lag_90": lag_value(90),
        "RollingMean_3": trailing_mean(3),
        "RollingMean_7": trailing_mean(7),
        "RollingMean_14": trailing_mean(14),
        "RollingMean_30": trailing_mean(30),
        "RollingStd_7": trailing_std(7),
        "RollingStd_14": trailing_std(14),
        "RollingStd_30": trailing_std(30),
        "RollingMedian": float(sales_history.tail(30).median()) if len(sales_history) else 0.0,
        "RollingMax": float(sales_history.tail(30).max()) if len(sales_history) else 0.0,
        "RollingMin": float(sales_history.tail(30).min()) if len(sales_history) else 0.0,
        "ExpandingMean": float(sales_history.mean()) if len(sales_history) else 0.0,
        "ExpandingStd": float(sales_history.std(ddof=0)) if len(sales_history) > 1 else 0.0,
        "Day": int(future_date.day),
        "Week": int(future_date.isocalendar().week),
        "Month": int(future_date.month),
        "Quarter": int(future_date.quarter),
        "Year": int(future_date.year),
        "WeekOfYear": int(future_date.isocalendar().week),
        "DayOfWeek": int(future_date.dayofweek),
        "DayOfMonth": int(future_date.day),
        "MonthStart": int(future_date.is_month_start),
        "MonthEnd": int(future_date.is_month_end),
        "QuarterStart": int(future_date.is_quarter_start),
        "QuarterEnd": int(future_date.is_quarter_end),
        "Weekend": int(future_date.dayofweek in {5, 6}),
        "SeasonCode": int(SEASON_CODE[season_name]),
        "Holiday": int(build_holiday_flag(pd.Series([future_date])).iloc[0]),
        "MonthlyRevenue": monthly_revenue,
        "MonthlyDemand": monthly_demand,
        "CountryDemand": float(context.get("CountryDemand", monthly_demand)),
        "CategoryDemand": float(context.get("CategoryDemand", monthly_demand)),
        "ProductDemand": float(context.get("ProductDemand", monthly_demand)),
        "AverageOrderValue": float(average_order_value),
        "BasketSize": float(basket_size),
        "CustomerFrequency": float(customer_history.tail(30).mean()) if len(customer_history) else 0.0,
        "ProductFrequency": float(orders_history.tail(30).sum()) if len(orders_history) else 0.0,
        "DailyGrowth": safe_pct_change(last_value, prior_value),
        "WeeklyGrowth": safe_pct_change(rolling_week, previous_week),
        "MonthlyGrowth": safe_pct_change(rolling_month, previous_month),
    }


def fit_final_models(
    prepared_df: pd.DataFrame,
    selected_frames: dict[str, pd.DataFrame],
    best_model_name: str,
    configuration: str,
    selected_features: Sequence[str],
    params_by_model: dict[str, dict[str, Any]],
    backtest_results: pd.DataFrame,
) -> dict[str, FittedModelBundle]:
    bundles: dict[str, FittedModelBundle] = {}
    params = params_by_model.get(best_model_name, {})

    for series_key, history in selected_frames.items():
        trainable = prepared_df[prepared_df["SeriesKey"] == series_key].copy()
        if trainable.empty:
            continue
        X = clean_feature_matrix(trainable, feature_columns())
        y = pd.to_numeric(trainable["Target"], errors="coerce").fillna(0).astype(float)
        bundle = fit_model(
            model_name=best_model_name,
            X_train=X,
            y_train=y,
            train_dates=pd.to_datetime(trainable["Date"]),
            selected_features=selected_features,
            params=params,
        )
        residuals = (
            backtest_results.loc[backtest_results["SeriesKey"] == series_key, "Residual"]
            if not backtest_results.empty
            else pd.Series(dtype=float)
        )
        residual_std = float(residuals.std(ddof=0)) if not residuals.empty else float(history["Sales"].std(ddof=0))
        last_row = trainable.iloc[-1]
        avg_unit_price = float(history["AvgUnitPriceSeries"].iloc[-1]) if "AvgUnitPriceSeries" in history.columns else 0.0
        if avg_unit_price <= 0:
            total_sales = float(history["Sales"].sum())
            total_revenue = float(history["Revenue"].sum())
            avg_unit_price = total_revenue / total_sales if total_sales > 0 else 0.0
        bundle.metadata.update(
            {
                "series_key": series_key,
                "configuration": configuration,
                "residual_std": residual_std if np.isfinite(residual_std) else 0.0,
                "avg_unit_price": avg_unit_price,
                "avg_orders": float(history["Orders"].tail(30).mean()),
                "avg_customers": float(history["UniqueCustomers"].tail(30).mean()),
                "CountryDemand": float(last_row.get("CountryDemand", 0.0)),
                "CategoryDemand": float(last_row.get("CategoryDemand", 0.0)),
                "ProductDemand": float(last_row.get("ProductDemand", 0.0)),
                "AverageOrderValue": float(last_row.get("AverageOrderValue", 0.0)),
                "BasketSize": float(last_row.get("BasketSize", 0.0)),
            }
        )
        bundles[series_key] = bundle
    return bundles


def recursive_forecast_series(
    series_history: pd.DataFrame,
    bundle: FittedModelBundle,
    horizon: int,
) -> pd.DataFrame:
    history = series_history.sort_values("Date").copy()
    history = history.loc[:, ["Date", "Sales", "Revenue", "Orders", "UniqueCustomers"]].reset_index(drop=True)
    context = {
        "CountryDemand": float(bundle.metadata.get("CountryDemand", 0.0)),
        "CategoryDemand": float(bundle.metadata.get("CategoryDemand", 0.0)),
        "ProductDemand": float(bundle.metadata.get("ProductDemand", 0.0)),
        "AverageOrderValue": float(bundle.metadata.get("AverageOrderValue", 0.0)),
        "BasketSize": float(bundle.metadata.get("BasketSize", 0.0)),
    }
    residual_std = float(bundle.metadata.get("residual_std", 0.0))
    avg_unit_price = float(bundle.metadata.get("avg_unit_price", 0.0))
    avg_orders = float(bundle.metadata.get("avg_orders", 0.0))
    avg_customers = float(bundle.metadata.get("avg_customers", 0.0))
    future_dates = pd.date_range(pd.Timestamp(history["Date"].max()) + pd.Timedelta(days=1), periods=horizon, freq="D")
    rows: list[dict[str, Any]] = []

    if bundle.kind in {"statsmodels", "prophet", "autoarima"}:
        feature_frame = pd.DataFrame(index=np.arange(horizon))
        predictions = predict_with_bundle(
            bundle=bundle,
            X_frame=feature_frame,
            future_dates=future_dates.tolist(),
            history=history["Sales"].tolist(),
        )
        for future_date, demand_value in zip(future_dates, predictions, strict=False):
            demand = max(0.0, float(demand_value))
            revenue = demand * avg_unit_price
            rows.append(
                {
                    "Date": future_date,
                    "ForecastDemand": demand,
                    "ForecastRevenue": revenue,
                    "Lower95Demand": max(0.0, demand - (1.96 * residual_std)),
                    "Upper95Demand": demand + (1.96 * residual_std),
                }
            )
        return pd.DataFrame(rows)

    if bundle.kind == "baseline":
        predictions = predict_baseline(bundle.model_name, history["Sales"].tolist(), horizon)
        for future_date, demand_value in zip(future_dates, predictions, strict=False):
            demand = max(0.0, float(demand_value))
            revenue = demand * avg_unit_price
            rows.append(
                {
                    "Date": future_date,
                    "ForecastDemand": demand,
                    "ForecastRevenue": revenue,
                    "Lower95Demand": max(0.0, demand - (1.96 * residual_std)),
                    "Upper95Demand": demand + (1.96 * residual_std),
                }
            )
        return pd.DataFrame(rows)

    for future_date in future_dates:
        feature_row = build_feature_row_from_history(history, future_date, context)
        feature_frame = pd.DataFrame([feature_row])
        prediction = predict_with_bundle(
            bundle=bundle,
            X_frame=feature_frame,
            future_dates=[future_date],
            history=history["Sales"].tolist(),
        )
        demand = max(0.0, float(prediction[0]))
        revenue = demand * avg_unit_price
        lower = max(0.0, demand - (1.96 * residual_std))
        upper = demand + (1.96 * residual_std)
        rows.append(
            {
                "Date": future_date,
                "ForecastDemand": demand,
                "ForecastRevenue": revenue,
                "Lower95Demand": lower,
                "Upper95Demand": upper,
            }
        )
        history = pd.concat(
            [
                history,
                pd.DataFrame(
                    [
                        {
                            "Date": future_date,
                            "Sales": demand,
                            "Revenue": revenue,
                            "Orders": avg_orders,
                            "UniqueCustomers": avg_customers,
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )

    return pd.DataFrame(rows)


def generate_future_predictions(
    selected_frames: dict[str, pd.DataFrame],
    fitted_models: dict[str, FittedModelBundle],
    horizons: Sequence[int],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    max_horizon = max(horizons)
    sku_rows: list[pd.DataFrame] = []

    for series_key, history in selected_frames.items():
        if series_key not in fitted_models:
            continue
        bundle = fitted_models[series_key]
        forecast = recursive_forecast_series(history, bundle, max_horizon)
        metadata = history.iloc[-1]
        forecast["SeriesKey"] = series_key
        forecast["Product"] = metadata["Description"]
        forecast["Country"] = metadata["Country"]
        forecast["ProductCategory"] = metadata["ProductCategory"]
        forecast["Model"] = bundle.model_name
        forecast["Configuration"] = bundle.metadata.get("configuration", "default")
        forecast["Entity"] = metadata["Description"]
        forecast["ForecastLevel"] = "SKU"
        sku_rows.append(forecast)

    if not sku_rows:
        return pd.DataFrame(), pd.DataFrame()

    sku_base = pd.concat(sku_rows, ignore_index=True)
    per_horizon_rows: list[pd.DataFrame] = []
    aggregated_rows: list[pd.DataFrame] = []

    for horizon in horizons:
        subset = sku_base.groupby("SeriesKey", sort=False).head(horizon).copy()
        subset["HorizonDays"] = horizon
        per_horizon_rows.append(subset)

        category = (
            subset.groupby(["Date", "HorizonDays", "ProductCategory", "Model", "Configuration"], as_index=False)
            .agg(
                ForecastDemand=("ForecastDemand", "sum"),
                ForecastRevenue=("ForecastRevenue", "sum"),
                Lower95Demand=("Lower95Demand", "sum"),
                Upper95Demand=("Upper95Demand", "sum"),
            )
            .rename(columns={"ProductCategory": "Entity"})
        )
        category["ForecastLevel"] = "Category"
        category["SeriesKey"] = "AGGREGATED"
        category["Product"] = "ALL"
        category["Country"] = "ALL"
        category["ProductCategory"] = category["Entity"]

        country = (
            subset.groupby(["Date", "HorizonDays", "Country", "Model", "Configuration"], as_index=False)
            .agg(
                ForecastDemand=("ForecastDemand", "sum"),
                ForecastRevenue=("ForecastRevenue", "sum"),
                Lower95Demand=("Lower95Demand", "sum"),
                Upper95Demand=("Upper95Demand", "sum"),
            )
            .rename(columns={"Country": "Entity"})
        )
        country["ForecastLevel"] = "Country"
        country["SeriesKey"] = "AGGREGATED"
        country["Product"] = "ALL"
        country["Country"] = country["Entity"]
        country["ProductCategory"] = "ALL"

        revenue = (
            subset.groupby(["Date", "HorizonDays", "Model", "Configuration"], as_index=False)
            .agg(
                ForecastDemand=("ForecastDemand", "sum"),
                ForecastRevenue=("ForecastRevenue", "sum"),
                Lower95Demand=("Lower95Demand", "sum"),
                Upper95Demand=("Upper95Demand", "sum"),
            )
        )
        revenue["ForecastLevel"] = "Revenue"
        revenue["Entity"] = "Global Revenue"
        revenue["SeriesKey"] = "AGGREGATED"
        revenue["Product"] = "ALL"
        revenue["Country"] = "ALL"
        revenue["ProductCategory"] = "ALL"

        demand = revenue.copy()
        demand["ForecastLevel"] = "Demand"
        demand["Entity"] = "Global Demand"

        aggregated_rows.extend([category, country, revenue, demand])

    future_predictions = pd.concat(per_horizon_rows + aggregated_rows, ignore_index=True)
    dashboard = (
        future_predictions.groupby(["HorizonDays", "ForecastLevel", "Entity"], as_index=False)
        .agg(ForecastDemand=("ForecastDemand", "sum"), ForecastRevenue=("ForecastRevenue", "sum"))
        .sort_values(["HorizonDays", "ForecastRevenue"], ascending=[True, False])
        .reset_index(drop=True)
    )
    dashboard["DemandRisk"] = np.where(
        dashboard["ForecastDemand"] >= dashboard["ForecastDemand"].quantile(0.75),
        "High",
        "Medium",
    )
    dashboard["RevenuePriority"] = np.where(
        dashboard["ForecastRevenue"] >= dashboard["ForecastRevenue"].quantile(0.75),
        "Priority",
        "Monitor",
    )
    return future_predictions, dashboard


def top_feature_importance(
    anchor_series: pd.DataFrame,
    best_model_name: str,
    selected_features: Sequence[str],
    params_by_model: dict[str, dict[str, Any]],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    columns = list(selected_features) if selected_features else feature_columns()
    X = clean_feature_matrix(anchor_series, columns)
    y = pd.to_numeric(anchor_series["Target"], errors="coerce").fillna(0).astype(float)
    split_idx = max(1, len(anchor_series) - DEFAULT_TEST_SIZE)
    X_train = X.iloc[:split_idx]
    y_train = y.iloc[:split_idx]
    X_test = X.iloc[split_idx:]
    y_test = y.iloc[split_idx:]
    params = params_by_model.get(best_model_name, {})

    if best_model_name in {"Naive", "Seasonal Naive", "Moving Average", "Prophet", "AutoARIMA"}:
        estimator = RandomForestRegressor(n_estimators=250, random_state=42, n_jobs=-1)
        estimator.fit(X_train, y_train)
        model_for_explainability = estimator
        explanation_source = "Surrogate Random Forest"
    else:
        bundle = fit_model(
            model_name=best_model_name,
            X_train=X_train,
            y_train=y_train,
            train_dates=pd.to_datetime(anchor_series.iloc[:split_idx]["Date"]),
            selected_features=columns,
            params=params,
        )
        if bundle.kind != "supervised":
            estimator = RandomForestRegressor(n_estimators=250, random_state=42, n_jobs=-1)
            estimator.fit(X_train, y_train)
            model_for_explainability = estimator
            explanation_source = "Surrogate Random Forest"
        else:
            model_for_explainability = bundle.estimator
            explanation_source = best_model_name

    if hasattr(model_for_explainability, "named_steps"):
        regressor = model_for_explainability.named_steps["regressor"]
    else:
        regressor = model_for_explainability

    if hasattr(regressor, "feature_importances_"):
        importance_values = regressor.feature_importances_
    elif hasattr(regressor, "coef_"):
        coef = np.asarray(regressor.coef_, dtype=float).reshape(-1)
        importance_values = np.abs(coef)
    else:
        importance_values = np.zeros(len(columns), dtype=float)

    feature_importance_df = (
        pd.DataFrame(
            {
                "feature": columns,
                "importance": importance_values,
                "source_model": explanation_source,
            }
        )
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )

    if len(X_test) > 0:
        permutation = permutation_importance(
            model_for_explainability,
            X_test,
            y_test,
            n_repeats=8,
            random_state=42,
        )
        permutation_df = (
            pd.DataFrame(
                {
                    "feature": columns,
                    "importance_mean": permutation.importances_mean,
                    "importance_std": permutation.importances_std,
                }
            )
            .sort_values("importance_mean", ascending=False)
            .reset_index(drop=True)
        )
    else:
        permutation_df = pd.DataFrame(columns=["feature", "importance_mean", "importance_std"])

    shap_df = pd.DataFrame(columns=["feature", "mean_abs_shap"])
    if shap is not None and len(X_test) > 0:
        try:  # pragma: no cover - optional dependency
            explainer = shap.Explainer(model_for_explainability.predict, X_train)
            values = explainer(X_test)
            shap_df = (
                pd.DataFrame(
                    {
                        "feature": columns,
                        "mean_abs_shap": np.abs(values.values).mean(axis=0),
                    }
                )
                .sort_values("mean_abs_shap", ascending=False)
                .reset_index(drop=True)
            )
        except Exception as exc:  # pragma: no cover - optional dependency
            logger.warning("SHAP computation failed: %s", exc)

    return feature_importance_df, permutation_df, shap_df


def create_tensorflow_sequences(values: np.ndarray, lookback: int) -> tuple[np.ndarray, np.ndarray]:
    X, y = [], []
    for idx in range(lookback, len(values)):
        X.append(values[idx - lookback : idx])
        y.append(values[idx])
    if not X:
        return np.empty((0, lookback, 1)), np.empty((0,))
    features = np.asarray(X, dtype=float)[..., np.newaxis]
    targets = np.asarray(y, dtype=float)
    return features, targets


def build_tensorflow_model(model_name: str, lookback: int) -> Any:
    if tf is None or layers is None or models is None:
        return None
    model = models.Sequential()
    model.add(layers.Input(shape=(lookback, 1)))
    if model_name == "LSTM":
        model.add(layers.LSTM(64))
    elif model_name == "Bidirectional LSTM":
        model.add(layers.Bidirectional(layers.LSTM(64)))
    elif model_name == "GRU":
        model.add(layers.GRU(64))
    else:
        model.add(layers.Conv1D(32, kernel_size=3, activation="relu"))
        model.add(layers.MaxPooling1D(pool_size=2))
        model.add(layers.LSTM(32))
    model.add(layers.Dense(32, activation="relu"))
    model.add(layers.Dense(1))
    model.compile(optimizer="adam", loss="mae", metrics=["mae"])
    return model


def run_deep_learning_suite(
    anchor_series: pd.DataFrame,
    models_dir: Path,
) -> tuple[pd.DataFrame, dict[str, Path], pd.DataFrame]:
    columns = ["LSTM", "Bidirectional LSTM", "GRU", "CNN-LSTM"]
    artifact_paths: dict[str, Path] = {}
    history_rows: list[dict[str, Any]] = []

    if tf is None or keras_callbacks is None:
        rows = [
            {
                "model_name": name,
                "configuration": "default",
                "series_key": anchor_series["SeriesKey"].iloc[0] if not anchor_series.empty else "ALL",
                "status": "unavailable",
                "reason": "tensorflow is not installed",
                "mae": np.nan,
                "rmse": np.nan,
                "mape": np.nan,
                "smape": np.nan,
                "r2": np.nan,
                "mase": np.nan,
                "parameters": "{}",
            }
            for name in columns
        ]
        return pd.DataFrame(rows), artifact_paths, pd.DataFrame()

    values = pd.to_numeric(anchor_series["Target"], errors="coerce").fillna(0).astype(float).to_numpy()
    if len(values) < 120:
        return pd.DataFrame(), artifact_paths, pd.DataFrame()

    lookback = 30
    mean_value = float(values.mean())
    std_value = float(values.std()) or 1.0
    scaled = (values - mean_value) / std_value
    X, y = create_tensorflow_sequences(scaled, lookback)
    if len(X) < 40:
        return pd.DataFrame(), artifact_paths, pd.DataFrame()

    split_idx = max(1, int(len(X) * 0.8))
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]
    metrics_rows: list[dict[str, Any]] = []

    filename_map = {
        "LSTM": "lstm_model.keras",
        "Bidirectional LSTM": "bilstm_model.keras",
        "GRU": "gru_model.keras",
        "CNN-LSTM": "cnn_lstm_model.keras",
    }

    for model_name in columns:
        model = build_tensorflow_model(model_name, lookback)
        if model is None:
            continue
        model_path = models_dir / filename_map[model_name]
        model_path.parent.mkdir(parents=True, exist_ok=True)
        checkpoint = keras_callbacks.ModelCheckpoint(model_path, save_best_only=True, monitor="val_loss")
        early_stopping = keras_callbacks.EarlyStopping(patience=8, restore_best_weights=True, monitor="val_loss")
        reduce_lr = keras_callbacks.ReduceLROnPlateau(patience=4, factor=0.5, monitor="val_loss")

        history = model.fit(
            X_train,
            y_train,
            validation_data=(X_val, y_val),
            epochs=40,
            batch_size=32,
            verbose=0,
            callbacks=[checkpoint, early_stopping, reduce_lr],
        )
        predictions = model.predict(X_val, verbose=0).reshape(-1)
        y_true = (y_val * std_value) + mean_value
        y_pred = (predictions * std_value) + mean_value
        metrics = evaluate_predictions(y_true, y_pred)
        metrics_rows.append(
            {
                "model_name": model_name,
                "configuration": "default",
                "series_key": anchor_series["SeriesKey"].iloc[0],
                "status": "evaluated",
                "reason": "",
                **metrics,
                "parameters": json_dumps_safe({"lookback": lookback, "epochs": 40, "batch_size": 32}),
            }
        )
        artifact_paths[slugify(model_name)] = model_path
        for epoch_idx, (loss, val_loss) in enumerate(
            zip(history.history.get("loss", []), history.history.get("val_loss", []), strict=False),
            start=1,
        ):
            history_rows.append(
                {
                    "model_name": model_name,
                    "epoch": epoch_idx,
                    "loss": float(loss),
                    "val_loss": float(val_loss),
                }
            )

    return pd.DataFrame(metrics_rows), artifact_paths, pd.DataFrame(history_rows)


def add_prediction_intervals(results: pd.DataFrame) -> pd.DataFrame:
    if results.empty:
        return results
    enriched = results.copy()
    std_map = (
        enriched.groupby("SeriesKey")["Residual"].std(ddof=0).fillna(0).to_dict()
    )
    enriched["ResidualStd"] = enriched["SeriesKey"].map(std_map).fillna(0)
    enriched["Lower95"] = np.maximum(0.0, enriched["Forecast"] - (1.96 * enriched["ResidualStd"]))
    enriched["Upper95"] = enriched["Forecast"] + (1.96 * enriched["ResidualStd"])
    return enriched


def create_visualizations(
    historical_daily: pd.DataFrame,
    backtest_results: pd.DataFrame,
    leaderboard: pd.DataFrame,
    future_predictions: pd.DataFrame,
    feature_importance_df: pd.DataFrame,
    permutation_df: pd.DataFrame,
    shap_df: pd.DataFrame,
    figures_dir: Path,
    deep_learning_history: pd.DataFrame,
) -> list[Path]:
    figures_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")
    paths: list[Path] = []
    counter = 1

    def save(fig: plt.Figure, name: str) -> Path:
        nonlocal counter
        filename = f"forecast_{counter:02d}_{slugify(name)}.png"
        path = figures_dir / filename
        backup_existing_file(path)
        fig.tight_layout()
        fig.savefig(path, dpi=250, bbox_inches="tight")
        plt.close(fig)
        paths.append(path)
        counter += 1
        return path

    top_leaderboard = leaderboard.head(10).copy()
    if not top_leaderboard.empty:
        for metric in ["rmse", "mae", "mape", "smape", "mase", "r2"]:
            fig, ax = plt.subplots(figsize=(12, 4))
            sns.barplot(data=top_leaderboard, x="model_name", y=metric, hue="configuration", ax=ax)
            ax.set_title(f"Leaderboard by {metric.upper()}")
            ax.tick_params(axis="x", rotation=45)
            save(fig, f"leaderboard_{metric}")

        fig, ax = plt.subplots(figsize=(10, 6))
        heatmap_data = top_leaderboard.set_index("model_name")[["rmse", "mae", "mape", "smape", "mase", "r2"]]
        sns.heatmap(heatmap_data, cmap="Blues", annot=True, fmt=".2f", ax=ax)
        ax.set_title("Model Comparison Heatmap")
        save(fig, "leaderboard_heatmap")

    if not backtest_results.empty:
        series_keys = backtest_results["SeriesKey"].drop_duplicates().head(5).tolist()
        for series_key in series_keys:
            subset = backtest_results[backtest_results["SeriesKey"] == series_key].copy()
            label = slugify(series_key[:40])

            fig, ax = plt.subplots(figsize=(12, 4))
            ax.plot(subset["Date"], subset["Actual"], label="Actual")
            ax.plot(subset["Date"], subset["Forecast"], label="Forecast")
            ax.fill_between(subset["Date"], subset["Lower95"], subset["Upper95"], alpha=0.2, label="95% interval")
            ax.set_title(f"Actual vs Forecast - {series_key}")
            ax.legend()
            save(fig, f"actual_vs_forecast_{label}")

            fig, ax = plt.subplots(figsize=(12, 4))
            ax.plot(subset["Date"], subset["Residual"], color="#d62728")
            ax.axhline(0, linestyle="--", color="black")
            ax.set_title(f"Residual Plot - {series_key}")
            save(fig, f"residual_plot_{label}")

            fig, ax = plt.subplots(figsize=(6, 6))
            sns.scatterplot(data=subset, x="Forecast", y="Actual", ax=ax)
            max_value = max(float(subset["Forecast"].max()), float(subset["Actual"].max()), 1.0)
            ax.plot([0, max_value], [0, max_value], linestyle="--", color="gray")
            ax.set_title(f"Prediction Error - {series_key}")
            save(fig, f"prediction_error_{label}")

            rolling = subset[["Date", "Actual", "Forecast"]].copy().sort_values("Date")
            rolling["ActualRolling"] = rolling["Actual"].rolling(window=14, min_periods=1).mean()
            rolling["ForecastRolling"] = rolling["Forecast"].rolling(window=14, min_periods=1).mean()
            fig, ax = plt.subplots(figsize=(12, 4))
            ax.plot(rolling["Date"], rolling["ActualRolling"], label="Actual 14D Mean")
            ax.plot(rolling["Date"], rolling["ForecastRolling"], label="Forecast 14D Mean")
            ax.set_title(f"Rolling Forecast - {series_key}")
            ax.legend()
            save(fig, f"rolling_forecast_{label}")

            fig, ax = plt.subplots(figsize=(10, 4))
            sns.histplot(subset["Residual"], bins=20, kde=True, ax=ax)
            ax.set_title(f"Residual Distribution - {series_key}")
            save(fig, f"residual_distribution_{label}")

    if not historical_daily.empty:
        daily_total = historical_daily.groupby("Date", as_index=False).agg(Sales=("Sales", "sum"), Revenue=("Revenue", "sum"))
        monthly_total = (
            daily_total.assign(Month=daily_total["Date"].dt.to_period("M").dt.to_timestamp())
            .groupby("Month", as_index=False)
            .agg(Sales=("Sales", "sum"), Revenue=("Revenue", "sum"))
        )
        weekly_total = (
            daily_total.assign(Week=daily_total["Date"].dt.to_period("W").dt.start_time)
            .groupby("Week", as_index=False)
            .agg(Sales=("Sales", "sum"), Revenue=("Revenue", "sum"))
        )
        yearly_total = (
            daily_total.assign(Year=daily_total["Date"].dt.year)
            .groupby("Year", as_index=False)
            .agg(Revenue=("Revenue", "sum"))
        )

        fig, ax = plt.subplots(figsize=(12, 4))
        ax.plot(daily_total["Date"], daily_total["Sales"])
        ax.set_title("Historical Daily Demand Trend")
        save(fig, "historical_daily_demand_trend")

        fig, ax = plt.subplots(figsize=(12, 4))
        ax.plot(daily_total["Date"], daily_total["Revenue"], color="#2ca02c")
        ax.set_title("Historical Daily Revenue Trend")
        save(fig, "historical_daily_revenue_trend")

        fig, ax = plt.subplots(figsize=(12, 4))
        ax.plot(monthly_total["Month"], monthly_total["Sales"], color="#ff7f0e")
        ax.set_title("Monthly Demand Trend")
        save(fig, "monthly_demand_trend")

        fig, ax = plt.subplots(figsize=(12, 4))
        ax.plot(monthly_total["Month"], monthly_total["Revenue"], color="#9467bd")
        ax.set_title("Monthly Revenue Trend")
        save(fig, "monthly_revenue_trend")

        fig, ax = plt.subplots(figsize=(12, 4))
        ax.plot(weekly_total["Week"], weekly_total["Sales"], color="#17becf")
        ax.set_title("Weekly Demand Trend")
        save(fig, "weekly_demand_trend")

        fig, ax = plt.subplots(figsize=(8, 4))
        sns.barplot(data=yearly_total, x="Year", y="Revenue", ax=ax)
        ax.set_title("Yearly Revenue Trend")
        save(fig, "yearly_revenue_trend")

        top_countries = (
            historical_daily.groupby("Country")["Revenue"].sum().sort_values(ascending=False).head(4).index.tolist()
        )
        for country in top_countries:
            subset = (
                historical_daily[historical_daily["Country"] == country]
                .groupby("Date", as_index=False)["Revenue"]
                .sum()
            )
            fig, ax = plt.subplots(figsize=(12, 4))
            ax.plot(subset["Date"], subset["Revenue"])
            ax.set_title(f"Country Trend - {country}")
            save(fig, f"country_trend_{country}")

        top_categories = (
            historical_daily.groupby("ProductCategory")["Revenue"].sum().sort_values(ascending=False).head(4).index.tolist()
        )
        for category in top_categories:
            subset = (
                historical_daily[historical_daily["ProductCategory"] == category]
                .groupby("Date", as_index=False)["Revenue"]
                .sum()
            )
            fig, ax = plt.subplots(figsize=(12, 4))
            ax.plot(subset["Date"], subset["Revenue"])
            ax.set_title(f"Category Trend - {category}")
            save(fig, f"category_trend_{category}")

        top_products = (
            historical_daily.groupby("Description")["Revenue"].sum().sort_values(ascending=False).head(4).index.tolist()
        )
        for product in top_products:
            subset = (
                historical_daily[historical_daily["Description"] == product]
                .groupby("Date", as_index=False)["Revenue"]
                .sum()
            )
            fig, ax = plt.subplots(figsize=(12, 4))
            ax.plot(subset["Date"], subset["Revenue"])
            ax.set_title(f"SKU Trend - {product}")
            save(fig, f"sku_trend_{product}")

    if not future_predictions.empty:
        sku_future = future_predictions[future_predictions["ForecastLevel"] == "SKU"].copy()
        for horizon in sorted(sku_future["HorizonDays"].dropna().unique().tolist()):
            subset = (
                sku_future[sku_future["HorizonDays"] == horizon]
                .groupby("Date", as_index=False)
                .agg(ForecastDemand=("ForecastDemand", "sum"), ForecastRevenue=("ForecastRevenue", "sum"))
            )
            fig, ax = plt.subplots(figsize=(12, 4))
            ax.plot(subset["Date"], subset["ForecastDemand"])
            ax.set_title(f"Forecast Horizon - {horizon} Days")
            save(fig, f"forecast_horizon_{horizon}")

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.histplot(sku_future["ForecastDemand"], bins=30, kde=True, ax=ax)
        ax.set_title("Forecast Distribution")
        save(fig, "forecast_distribution")

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.histplot(sku_future["ForecastRevenue"], bins=30, kde=True, ax=ax)
        ax.set_title("Revenue Forecast Distribution")
        save(fig, "revenue_forecast_distribution")

        horizon_compare = (
            sku_future.groupby("HorizonDays", as_index=False)
            .agg(ForecastDemand=("ForecastDemand", "sum"), ForecastRevenue=("ForecastRevenue", "sum"))
        )
        fig, ax = plt.subplots(figsize=(8, 4))
        sns.barplot(data=horizon_compare, x="HorizonDays", y="ForecastDemand", ax=ax)
        ax.set_title("Forecast Horizon Comparison")
        save(fig, "forecast_horizon_comparison")

        country_heatmap = (
            future_predictions[future_predictions["ForecastLevel"] == "Country"]
            .pivot_table(index="Entity", columns="HorizonDays", values="ForecastDemand", aggfunc="sum")
            .fillna(0)
        )
        if not country_heatmap.empty:
            fig, ax = plt.subplots(figsize=(8, 6))
            sns.heatmap(country_heatmap, cmap="YlGnBu", ax=ax)
            ax.set_title("Country Forecast Heatmap")
            save(fig, "country_forecast_heatmap")

        category_heatmap = (
            future_predictions[future_predictions["ForecastLevel"] == "Category"]
            .pivot_table(index="Entity", columns="HorizonDays", values="ForecastDemand", aggfunc="sum")
            .fillna(0)
        )
        if not category_heatmap.empty:
            fig, ax = plt.subplots(figsize=(8, 6))
            sns.heatmap(category_heatmap, cmap="OrRd", ax=ax)
            ax.set_title("Category Forecast Heatmap")
            save(fig, "category_forecast_heatmap")

        executive = (
            sku_future.groupby(["Product"], as_index=False)
            .agg(ForecastRevenue=("ForecastRevenue", "sum"))
            .sort_values("ForecastRevenue", ascending=False)
            .head(10)
        )
        fig, ax = plt.subplots(figsize=(12, 4))
        sns.barplot(data=executive, x="Product", y="ForecastRevenue", ax=ax)
        ax.set_title("Executive Dashboard Preview")
        ax.tick_params(axis="x", rotation=45)
        save(fig, "executive_dashboard_preview")

        business = (
            sku_future.groupby(["ProductCategory"], as_index=False)
            .agg(ForecastDemand=("ForecastDemand", "sum"))
            .sort_values("ForecastDemand", ascending=False)
        )
        fig, ax = plt.subplots(figsize=(10, 4))
        sns.barplot(data=business, x="ProductCategory", y="ForecastDemand", ax=ax)
        ax.set_title("Business Dashboard Preview")
        save(fig, "business_dashboard_preview")

    if not feature_importance_df.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(data=feature_importance_df.head(15), x="importance", y="feature", ax=ax)
        ax.set_title("Feature Importance")
        save(fig, "feature_importance")

    if not permutation_df.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(data=permutation_df.head(15), x="importance_mean", y="feature", ax=ax)
        ax.set_title("Permutation Importance")
        save(fig, "permutation_importance")

    if not shap_df.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(data=shap_df.head(15), x="mean_abs_shap", y="feature", ax=ax)
        ax.set_title("SHAP Values")
        save(fig, "shap_values")

    if not historical_daily.empty:
        daily_total = historical_daily.groupby("Date", as_index=False)["Sales"].sum()
        lagged = pd.DataFrame({"Sales": daily_total["Sales"]})
        for lag in range(1, 31):
            lagged[f"Lag_{lag}"] = lagged["Sales"].shift(lag)
        correlation = lagged.corr().loc[["Sales"], [f"Lag_{lag}" for lag in range(1, 31)]]
        fig, ax = plt.subplots(figsize=(12, 2.5))
        sns.heatmap(correlation, cmap="coolwarm", center=0, ax=ax)
        ax.set_title("Lag Correlation")
        save(fig, "lag_correlation")

    if not deep_learning_history.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.lineplot(data=deep_learning_history, x="epoch", y="loss", hue="model_name", ax=ax)
        ax.set_title("Deep Learning Loss Curve")
        save(fig, "deep_learning_loss_curve")

        fig, ax = plt.subplots(figsize=(10, 5))
        sns.lineplot(data=deep_learning_history, x="epoch", y="val_loss", hue="model_name", ax=ax)
        ax.set_title("Deep Learning Validation Curve")
        save(fig, "deep_learning_validation_curve")

    if len(paths) < 60 and not historical_daily.empty:
        weekly_country = (
            historical_daily.assign(Week=historical_daily["Date"].dt.to_period("W").dt.start_time)
            .groupby(["Week", "Country"], as_index=False)["Revenue"]
            .sum()
        )
        for country in weekly_country["Country"].drop_duplicates().head(10):
            if len(paths) >= 60:
                break
            subset = weekly_country[weekly_country["Country"] == country]
            fig, ax = plt.subplots(figsize=(12, 4))
            ax.plot(subset["Week"], subset["Revenue"])
            ax.set_title(f"Weekly Country Trend - {country}")
            save(fig, f"weekly_country_trend_{country}")

    return paths


def interpret_important_features(feature_importance_df: pd.DataFrame) -> list[str]:
    descriptions = feature_descriptions()
    lines: list[str] = []
    for row in feature_importance_df.head(10).itertuples(index=False):
        message = descriptions.get(row.feature, "This feature contributes meaningful forecasting signal.")
        lines.append(f"- **{row.feature}**: {message}")
    return lines


def dependency_status_markdown() -> str:
    checks = {
        "statsmodels": StatsARIMA is not None and StatsExponentialSmoothing is not None,
        "xgboost": XGBRegressor is not None,
        "lightgbm": LGBMRegressor is not None,
        "catboost": CatBoostRegressor is not None,
        "prophet": Prophet is not None,
        "pmdarima": auto_arima is not None,
        "tensorflow": tf is not None,
        "shap": shap is not None,
    }
    return "\n".join(f"- {name}: {'available' if available else 'unavailable'}" for name, available in checks.items())


def frame_to_markdown_like(df: pd.DataFrame, rows: int = 10) -> str:
    if df.empty:
        return "No rows available."
    return "```\n" + df.head(rows).to_string(index=False) + "\n```"


def write_reports(
    best_selection: dict[str, Any],
    leaderboard: pd.DataFrame,
    tuning_summary: pd.DataFrame,
    feature_importance_df: pd.DataFrame,
    permutation_df: pd.DataFrame,
    shap_df: pd.DataFrame,
    future_predictions: pd.DataFrame,
    reports_dir: Path,
    figures_dir: Path,
    deep_learning_metrics: pd.DataFrame,
) -> dict[str, Path]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    interpret_lines = "\n".join(interpret_important_features(feature_importance_df))
    sku_future = future_predictions[future_predictions["ForecastLevel"] == "SKU"].copy()

    horizon_summary = (
        sku_future.groupby("HorizonDays", as_index=False)
        .agg(ForecastDemand=("ForecastDemand", "sum"), ForecastRevenue=("ForecastRevenue", "sum"))
        .sort_values("HorizonDays")
    )
    top_sku = (
        sku_future.groupby("Product", as_index=False)
        .agg(ForecastRevenue=("ForecastRevenue", "sum"), ForecastDemand=("ForecastDemand", "sum"))
        .sort_values("ForecastRevenue", ascending=False)
    )
    top_country = (
        future_predictions[future_predictions["ForecastLevel"] == "Country"]
        .groupby("Entity", as_index=False)
        .agg(ForecastRevenue=("ForecastRevenue", "sum"), ForecastDemand=("ForecastDemand", "sum"))
        .sort_values("ForecastRevenue", ascending=False)
    )
    top_category = (
        future_predictions[future_predictions["ForecastLevel"] == "Category"]
        .groupby("Entity", as_index=False)
        .agg(ForecastRevenue=("ForecastRevenue", "sum"), ForecastDemand=("ForecastDemand", "sum"))
        .sort_values("ForecastRevenue", ascending=False)
    )

    report_paths = {
        "forecast_report": reports_dir / "forecast_report.md",
        "model_leaderboard": reports_dir / "model_leaderboard.md",
        "deep_learning_report": reports_dir / "deep_learning_report.md",
        "forecast_business_summary": reports_dir / "forecast_business_summary.md",
        "executive_forecast_report": reports_dir / "executive_forecast_report.md",
    }

    write_text(
        f"""# Forecast Report

## Overview
RetailPulse Phase 3.5 upgrades the existing forecasting workflow into a modular enterprise pipeline with advanced lag, rolling, expanding, calendar, and business features. The workflow uses rolling-origin backtesting, TimeSeriesSplit validation, hyperparameter search, recursive feature elimination, explainability outputs, and multi-horizon forecasting.

## Dependency Status
{dependency_status_markdown()}

## Best Model
- Selected model: **{best_selection['model_name']}**
- Configuration: **{best_selection['configuration']}**
- Rationale: {best_selection['reason']}

## Leaderboard Snapshot
{frame_to_markdown_like(leaderboard, rows=12)}

## Hyperparameter Optimization
{frame_to_markdown_like(tuning_summary, rows=10)}

## Feature Interpretation
{interpret_lines if interpret_lines else '- Feature importance was unavailable for this run.'}

## Explainability Tables
### Feature Importance
{frame_to_markdown_like(feature_importance_df, rows=15)}

### Permutation Importance
{frame_to_markdown_like(permutation_df, rows=15)}

### SHAP Summary
{frame_to_markdown_like(shap_df, rows=15)}

## Forecast Horizon Summary
{frame_to_markdown_like(horizon_summary, rows=10)}

## Visual Assets
Generated figures are available under `{figures_dir}`.
""",
        report_paths["forecast_report"],
    )

    write_text(
        f"""# Model Leaderboard

## Ranked Models
{frame_to_markdown_like(leaderboard, rows=20)}

## Tuning Summary
{frame_to_markdown_like(tuning_summary, rows=20)}
""",
        report_paths["model_leaderboard"],
    )

    deep_body = (
        frame_to_markdown_like(deep_learning_metrics, rows=20)
        if not deep_learning_metrics.empty
        else "TensorFlow/Keras models were skipped because `tensorflow` is unavailable in this environment."
    )
    write_text(
        f"""# Deep Learning Report

The pipeline includes ready-to-run TensorFlow/Keras hooks for sequence windowing, normalization, EarlyStopping, ModelCheckpoint, and ReduceLROnPlateau across LSTM, Bidirectional LSTM, GRU, and CNN-LSTM architectures.

## Execution Status
{deep_body}
""",
        report_paths["deep_learning_report"],
    )

    write_text(
        f"""# Forecast Business Summary

## Horizon Outlook
{frame_to_markdown_like(horizon_summary, rows=10)}

## Top SKU Opportunities
{frame_to_markdown_like(top_sku, rows=10)}

## Top Countries
{frame_to_markdown_like(top_country, rows=10)}

## Top Categories
{frame_to_markdown_like(top_category, rows=10)}
""",
        report_paths["forecast_business_summary"],
    )

    write_text(
        f"""# Executive Forecast Report

The enterprise forecasting engine selected **{best_selection['model_name']}** in **{best_selection['configuration']}** configuration. The model outperformed the baseline portfolio under rolling-origin validation and now supports 30, 60, 90, 180, and 365-day demand and revenue views.

Key leadership takeaways:
- Forecasting now includes SKU, category, country, demand, and revenue perspectives.
- Model selection is evidence-based through leaderboard benchmarking and tuning.
- Explainability outputs identify the commercial drivers behind winning forecasts.
- Visual diagnostics are stored in `{figures_dir}` for operational and executive review.
""",
        report_paths["executive_forecast_report"],
    )

    return report_paths


def save_artifacts(
    leaderboard: pd.DataFrame,
    metrics: pd.DataFrame,
    backtest_results: pd.DataFrame,
    future_predictions: pd.DataFrame,
    dashboard: pd.DataFrame,
    fitted_models: dict[str, FittedModelBundle],
    best_selection: dict[str, Any],
    output_dir: Path,
    models_dir: Path,
    deep_learning_artifacts: dict[str, Path],
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)

    artifact_paths = {
        "leaderboard": output_dir / "leaderboard.csv",
        "forecast_results": output_dir / "forecast_results.csv",
        "forecast_metrics": output_dir / "forecast_metrics.csv",
        "future_predictions": output_dir / "future_predictions.csv",
        "forecast_dashboard": output_dir / "forecast_dashboard.csv",
        "best_forecast_model": models_dir / "best_forecast_model.pkl",
        "forecast_pipeline": models_dir / "forecast_pipeline.pkl",
        "forecast_scaler": models_dir / "forecast_scaler.pkl",
    }

    write_dataframe(leaderboard, artifact_paths["leaderboard"])
    write_dataframe(backtest_results, artifact_paths["forecast_results"])
    write_dataframe(metrics, artifact_paths["forecast_metrics"])
    write_dataframe(future_predictions, artifact_paths["future_predictions"])
    write_dataframe(dashboard, artifact_paths["forecast_dashboard"])

    serializable_models: dict[str, Any] = {}
    scaler_object: Any = None
    for series_key, bundle in fitted_models.items():
        if hasattr(bundle.estimator, "named_steps") and "scaler" in bundle.estimator.named_steps and scaler_object is None:
            scaler_object = bundle.estimator.named_steps["scaler"]
        serializable_models[series_key] = {
            "model_name": bundle.model_name,
            "kind": bundle.kind,
            "selected_features": bundle.selected_features,
            "params": bundle.params,
            "metadata": bundle.metadata,
            "estimator": bundle.estimator,
        }

    pipeline_payload = {
        "best_model_name": best_selection["model_name"],
        "configuration": best_selection["configuration"],
        "selected_features": next(iter(fitted_models.values())).selected_features if fitted_models else feature_columns(),
        "all_feature_columns": feature_columns(),
        "deep_learning_artifacts": {key: str(path) for key, path in deep_learning_artifacts.items()},
    }
    model_payload = {
        "best_model_name": best_selection["model_name"],
        "configuration": best_selection["configuration"],
        "reason": best_selection["reason"],
        "series_models": serializable_models,
    }
    scaler_payload = (
        scaler_object
        if scaler_object is not None
        else {
            "status": "not_required",
            "model_name": best_selection["model_name"],
            "reason": "The selected forecasting model family does not require a persisted sklearn scaler.",
        }
    )

    write_joblib(model_payload, artifact_paths["best_forecast_model"])
    write_joblib(pipeline_payload, artifact_paths["forecast_pipeline"])
    write_joblib(scaler_payload, artifact_paths["forecast_scaler"])

    for key, path in deep_learning_artifacts.items():
        artifact_paths[key] = path
    return artifact_paths


def run_enhanced_forecasting(
    input_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    reports_dir: str | Path | None = None,
    figures_dir: str | Path | None = None,
    models_dir: str | Path | None = None,
    *,
    top_n_series: int = DEFAULT_TOP_N_SERIES,
    min_history: int = DEFAULT_MIN_HISTORY,
    horizons: Sequence[int] = DEFAULT_HORIZONS,
    model_names: Sequence[str] | None = None,
) -> dict[str, Any]:
    logger.info("Running RetailPulse Phase 3.5 enterprise forecasting workflow")
    project_root = Path(__file__).resolve().parents[1]
    dataset_path = Path(input_path) if input_path is not None else project_root / "data" / "processed" / "final_processed_dataset.csv"
    if not dataset_path.exists():
        raise FileNotFoundError(f"Processed dataset not found at {dataset_path}")

    raw_df = pd.read_csv(dataset_path, parse_dates=["InvoiceDate"])
    prepared_df, selected_meta, historical_daily, selected_frames = prepare_feature_dataset(
        raw_df,
        top_n_series=top_n_series,
        min_history=min_history,
    )
    specs = model_catalog()
    available_default_models = [
        name
        for name, spec in specs.items()
        if spec.available and spec.family != "deep_learning"
    ]
    active_models = list(model_names) if model_names is not None else available_default_models
    initial_metrics, _ = evaluate_model_set(
        prepared_df=prepared_df,
        model_names=active_models,
        configuration="default",
        selected_features=feature_columns(),
    )
    unavailable_rows = unavailable_model_rows()
    metrics_df = pd.concat([initial_metrics, unavailable_rows], ignore_index=True, sort=False)
    leaderboard = aggregate_leaderboard(metrics_df)

    anchor_key = selected_meta.iloc[0]["SeriesKey"]
    anchor_series = prepared_df[prepared_df["SeriesKey"] == anchor_key].copy()
    tuning_summary, tuned_features, rfe_ranking, tuned_params = tune_models(anchor_series, tuning_candidate_names(leaderboard))

    tuned_metrics = pd.DataFrame()
    tuned_leaderboard = pd.DataFrame()
    if tuned_params:
        tuned_metrics, _ = evaluate_model_set(
            prepared_df=prepared_df,
            model_names=list(tuned_params.keys()),
            configuration="tuned",
            selected_features=tuned_features,
            params_by_model=tuned_params,
        )
        metrics_df = pd.concat([metrics_df, tuned_metrics], ignore_index=True, sort=False)
        tuned_leaderboard = aggregate_leaderboard(tuned_metrics)
        leaderboard = pd.concat([leaderboard, tuned_leaderboard], ignore_index=True, sort=False)
        leaderboard = leaderboard.sort_values(["rmse", "mae", "mape"], ascending=True).reset_index(drop=True)

    deep_learning_metrics, deep_learning_artifacts, deep_learning_history = run_deep_learning_suite(
        anchor_series=anchor_series,
        models_dir=Path(models_dir) if models_dir is not None else project_root / "models",
    )
    if not deep_learning_metrics.empty:
        metrics_df = pd.concat([metrics_df, deep_learning_metrics], ignore_index=True, sort=False)
        leaderboard = aggregate_leaderboard(metrics_df)

    best_selection = select_best_model(leaderboard)
    best_model_name = best_selection["model_name"]
    best_configuration = best_selection["configuration"]
    selected_features_for_best = tuned_features if best_configuration == "tuned" and best_model_name in tuned_params else feature_columns()
    params_by_model = tuned_params if best_configuration == "tuned" else {}

    _, best_backtest_results = evaluate_model_set(
        prepared_df=prepared_df,
        model_names=[best_model_name],
        configuration=best_configuration,
        selected_features=selected_features_for_best,
        params_by_model=params_by_model,
        collect_best_predictions_for=best_model_name,
    )
    best_backtest_results = add_prediction_intervals(best_backtest_results)

    fitted_models = fit_final_models(
        prepared_df=prepared_df,
        selected_frames=selected_frames,
        best_model_name=best_model_name,
        configuration=best_configuration,
        selected_features=selected_features_for_best,
        params_by_model=params_by_model,
        backtest_results=best_backtest_results,
    )
    future_predictions, dashboard = generate_future_predictions(
        selected_frames=selected_frames,
        fitted_models=fitted_models,
        horizons=tuple(horizons),
    )

    feature_importance_df, permutation_df, shap_df = top_feature_importance(
        anchor_series=anchor_series,
        best_model_name=best_model_name,
        selected_features=selected_features_for_best,
        params_by_model=params_by_model,
    )

    output_path = Path(output_dir) if output_dir is not None else project_root / "processed"
    reports_path = Path(reports_dir) if reports_dir is not None else project_root / "reports"
    figures_path = Path(figures_dir) if figures_dir is not None else reports_path / "figures"
    models_path = Path(models_dir) if models_dir is not None else project_root / "models"

    figures = create_visualizations(
        historical_daily=historical_daily,
        backtest_results=best_backtest_results,
        leaderboard=leaderboard,
        future_predictions=future_predictions,
        feature_importance_df=feature_importance_df,
        permutation_df=permutation_df,
        shap_df=shap_df,
        figures_dir=figures_path,
        deep_learning_history=deep_learning_history,
    )
    reports = write_reports(
        best_selection=best_selection,
        leaderboard=leaderboard,
        tuning_summary=tuning_summary,
        feature_importance_df=feature_importance_df,
        permutation_df=permutation_df,
        shap_df=shap_df,
        future_predictions=future_predictions,
        reports_dir=reports_path,
        figures_dir=figures_path,
        deep_learning_metrics=deep_learning_metrics,
    )
    artifacts = save_artifacts(
        leaderboard=leaderboard,
        metrics=metrics_df,
        backtest_results=best_backtest_results,
        future_predictions=future_predictions,
        dashboard=dashboard,
        fitted_models=fitted_models,
        best_selection=best_selection,
        output_dir=output_path,
        models_dir=models_path,
        deep_learning_artifacts=deep_learning_artifacts,
    )

    try:
        from mlflow_utils import SafeMLflowRun, log_parameter, log_metric, log_artifact
        with SafeMLflowRun("RetailPulse Forecasting", "enhanced_forecasting_run"):
            log_parameter("best_model_name", best_model_name)
            log_parameter("best_configuration", best_configuration)
            log_parameter("best_reason", best_selection.get("reason", ""))
            log_parameter("top_n_series", top_n_series)
            log_parameter("pipeline_type", "enhanced")
            
            if leaderboard is not None and not leaderboard.empty:
                for _, row in leaderboard.iterrows():
                    m_name = f"{row['model_name']}_{row['configuration']}".replace(" ", "_")
                    log_metric(f"enhanced_{m_name}_rmse", row["rmse"])
                    log_metric(f"enhanced_{m_name}_mae", row["mae"])
                    log_metric(f"enhanced_{m_name}_mape", row["mape"])
                    
            for path in artifacts.values():
                log_artifact(path, "csv_outputs")
            for path in reports.values():
                log_artifact(path, "reports")
            for path in figures.values():
                log_artifact(path, "plots")
    except Exception as e:
        logger.warning(f"Failed to log Phase 3.5 enhanced run to MLflow: {e}")

    return {
        "leaderboard": leaderboard,
        "metrics": metrics_df,
        "best_model": best_model_name,
        "best_configuration": best_configuration,
        "best_reason": best_selection["reason"],
        "selected_series": selected_meta,
        "backtest_results": best_backtest_results,
        "future_predictions": future_predictions,
        "forecast_dashboard": dashboard,
        "tuning_summary": tuning_summary,
        "rfe_ranking": rfe_ranking,
        "feature_importance": feature_importance_df,
        "permutation_importance": permutation_df,
        "shap_summary": shap_df,
        "artifact_paths": artifacts,
        "report_paths": reports,
        "visual_paths": figures,
        "deep_learning_metrics": deep_learning_metrics,
    }
