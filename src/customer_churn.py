from __future__ import annotations

import json
import math
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import AdaBoostClassifier, ExtraTreesClassifier, GradientBoostingClassifier, RandomForestClassifier, RandomForestRegressor
from sklearn.feature_selection import RFE
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    log_loss,
    matthews_corrcoef,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, StratifiedKFold, train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.neural_network import MLPClassifier

from chart_utils import draw_radar_chart, draw_simple_treemap, draw_waterfall
from config import FINAL_PROCESSED_DATA_PATH
from constants import DEFAULT_RANDOM_STATE
from io_utils import save_figure as persist_figure, slugify, write_dataframe, write_joblib, write_text
from logger import get_logger
from notebook_utils import make_notebook_cell, write_notebook_json
from report_utils import frame_to_markdown_like
from retail_rules import normalize_retail_frame

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid")

logger = get_logger(__name__)

try:  # pragma: no cover - optional dependency
    from xgboost import XGBClassifier
except Exception:  # pragma: no cover - optional dependency
    XGBClassifier = None

try:  # pragma: no cover - optional dependency
    from lightgbm import LGBMClassifier
except Exception:  # pragma: no cover - optional dependency
    LGBMClassifier = None

try:  # pragma: no cover - optional dependency
    from catboost import CatBoostClassifier
except Exception:  # pragma: no cover - optional dependency
    CatBoostClassifier = None

try:  # pragma: no cover - optional dependency
    import shap
except Exception:  # pragma: no cover - optional dependency
    shap = None

try:  # pragma: no cover - optional dependency
    from lime.lime_tabular import LimeTabularExplainer
except Exception:  # pragma: no cover - optional dependency
    LimeTabularExplainer = None


DEFAULT_CHURN_WINDOWS: tuple[int, ...] = (30, 60, 90, 180)
DEFAULT_PRIMARY_WINDOW = 90
DEFAULT_HEALTH_BUCKETS = (20, 40, 60, 80)
MODEL_SEARCH_RANDOM_ITERATIONS = 4
MODEL_SEARCH_CV_SPLITS = 3
MAX_FEATURES_FOR_RFE = 18
TARGET_VISUAL_COUNT = 80


@dataclass(frozen=True)
class ChurnModelSpec:
    name: str
    factory: Callable[[], Any] | None
    scale: bool = False
    random_grid: dict[str, Sequence[Any]] = field(default_factory=dict)
    grid: dict[str, Sequence[Any]] = field(default_factory=dict)
    available: bool = True
    reason_unavailable: str | None = None


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    if denominator == 0:
        return float(default)
    return float(numerator / denominator)


def safe_percentile(series: pd.Series) -> pd.Series:
    if series.empty:
        return pd.Series(dtype=float)
    ranks = series.rank(method="average", pct=True).fillna(0.0)
    return ranks.astype(float)


def mode_or_default(series: pd.Series, default: Any) -> Any:
    clean = series.dropna()
    if clean.empty:
        return default
    mode = clean.mode()
    if mode.empty:
        return clean.iloc[0]
    return mode.iloc[0]


def safe_trend(values: Sequence[float]) -> float:
    clean_values = [float(value) for value in values if pd.notna(value)]
    if len(clean_values) < 2:
        return 0.0
    x_values = np.arange(len(clean_values), dtype=float)
    slope = np.polyfit(x_values, np.asarray(clean_values, dtype=float), 1)[0]
    mean_value = float(np.mean(np.abs(clean_values)))
    return float(slope / (mean_value + 1e-6))


def safe_change(current: float, previous: float) -> float:
    if previous == 0:
        return 0.0 if current == 0 else 1.0
    return float((current - previous) / abs(previous))


def normalize_probability(values: pd.Series) -> pd.Series:
    if values.empty:
        return values.astype(float)
    minimum = float(values.min())
    maximum = float(values.max())
    if math.isclose(minimum, maximum):
        return pd.Series(np.full(len(values), 0.5), index=values.index, dtype=float)
    return ((values - minimum) / (maximum - minimum)).clip(0, 1)


def classification_pipeline(estimator: Any, *, scale: bool = False) -> Pipeline:
    steps: list[tuple[str, Any]] = [("imputer", SimpleImputer(strategy="median"))]
    if scale:
        steps.append(("scaler", StandardScaler()))
    steps.append(("classifier", estimator))
    return Pipeline(steps)


def regression_pipeline(estimator: Any, *, scale: bool = False) -> Pipeline:
    steps: list[tuple[str, Any]] = [("imputer", SimpleImputer(strategy="median"))]
    if scale:
        steps.append(("scaler", StandardScaler()))
    steps.append(("regressor", estimator))
    return Pipeline(steps)


def customer_feature_descriptions() -> dict[str, str]:
    return {
        "DaysSinceLastPurchase": "Customers with a longer pause since their last order are more likely to churn.",
        "PurchaseGap": "Average time between purchases highlights natural reorder cadence.",
        "AverageInterpurchaseTime": "This measures how quickly customers usually return.",
        "PurchaseMomentum": "Momentum compares recent buying to the prior observation window.",
        "CustomerVelocity": "Higher velocity means customers buy more often within the same tenure.",
        "CustomerGrowthRate": "Growth captures whether spend is expanding or contracting.",
        "RevenueTrend": "Revenue trend signals whether wallet share is strengthening or fading.",
        "FrequencyTrend": "Frequency trend shows if purchase cadence is accelerating or slowing.",
        "RecencyTrend": "Recency trend increases when the time between orders is getting worse.",
        "CategoryDiversity": "Category breadth indicates how many product lines the customer explores.",
        "ProductDiversity": "Product breadth reflects assortment engagement and cross-sell potential.",
        "RepeatPurchaseRatio": "Repeat buyers tend to stay longer and respond better to retention offers.",
        "CustomerActivityScore": "Activity blends recency, frequency, and revenue into one urgency signal.",
        "CustomerEngagementScore": "Engagement rewards variety, repeat buying, and steady order behavior.",
        "RevenueConcentration": "Highly concentrated revenue can expose a customer to seasonal or one-off demand.",
        "RollingRevenue_90": "Trailing 90-day spend is a strong proxy for near-term retention value.",
        "RollingPurchaseFrequency_90": "Recent order cadence is a direct signal of customer stickiness.",
        "RollingBasketSize_90": "Basket size helps identify deeper shopping missions and upsell opportunities.",
        "CustomerHealthScore": "Health combines commercial value and behavioral stability on a 0-100 scale.",
        "ExpectedLifetimeValue": "Expected lifetime value estimates future commercial upside.",
        "RetentionProbability": "Retention probability is the probability the customer remains active.",
    }


def _build_invoice_summary(data: pd.DataFrame) -> pd.DataFrame:
    invoice_summary = (
        data.groupby(["CustomerID", "InvoiceNo"], as_index=False)
        .agg(
            InvoiceDate=("InvoiceDate", "min"),
            Revenue=("Revenue", "sum"),
            Quantity=("Quantity", "sum"),
            BasketSize=("Description", "size"),
            Country=("Country", "first"),
            ProductCategory=("ProductCategory", lambda series: mode_or_default(series, "Other")),
            Description=("Description", lambda series: mode_or_default(series, "Unknown")),
        )
        .sort_values(["CustomerID", "InvoiceDate", "InvoiceNo"])
        .reset_index(drop=True)
    )
    invoice_summary["InvoiceDate"] = pd.to_datetime(invoice_summary["InvoiceDate"], errors="coerce")
    return invoice_summary.dropna(subset=["InvoiceDate"]).copy()


def _compute_window_metrics(customer_invoices: pd.DataFrame, snapshot_date: pd.Timestamp, window_days: int) -> dict[str, float]:
    window_start = snapshot_date - pd.Timedelta(days=window_days)
    previous_window_start = snapshot_date - pd.Timedelta(days=window_days * 2)
    recent_mask = customer_invoices["InvoiceDate"] >= window_start
    previous_mask = (customer_invoices["InvoiceDate"] >= previous_window_start) & (customer_invoices["InvoiceDate"] < window_start)

    recent_invoices = customer_invoices.loc[recent_mask]
    previous_invoices = customer_invoices.loc[previous_mask]

    recent_revenue = float(recent_invoices["Revenue"].sum())
    previous_revenue = float(previous_invoices["Revenue"].sum())
    recent_orders = float(recent_invoices["InvoiceNo"].nunique())
    previous_orders = float(previous_invoices["InvoiceNo"].nunique())

    return {
        f"RollingRevenue_{window_days}": recent_revenue,
        f"RollingPurchaseFrequency_{window_days}": safe_divide(recent_orders, window_days, 0.0),
        f"RollingBasketSize_{window_days}": float(recent_invoices["BasketSize"].mean()) if not recent_invoices.empty else 0.0,
        f"RollingRevenueShare_{window_days}": safe_divide(recent_revenue, float(customer_invoices["Revenue"].sum()), 0.0),
        f"RecentOrderCount_{window_days}": recent_orders,
        f"PreviousOrderCount_{window_days}": previous_orders,
        f"RecentRevenue_{window_days}": recent_revenue,
        f"PreviousRevenue_{window_days}": previous_revenue,
    }


def _customer_monthly_series(customer_invoices: pd.DataFrame) -> tuple[list[float], list[float]]:
    monthly = (
        customer_invoices.assign(InvoiceMonth=customer_invoices["InvoiceDate"].dt.to_period("M"))
        .groupby("InvoiceMonth", as_index=False)
        .agg(MonthlyRevenue=("Revenue", "sum"), MonthlyOrders=("InvoiceNo", "nunique"))
        .sort_values("InvoiceMonth")
        .reset_index(drop=True)
    )
    return monthly["MonthlyRevenue"].tolist(), monthly["MonthlyOrders"].tolist()


def _customer_summary_row(customer_id: int, customer_invoices: pd.DataFrame, snapshot_date: pd.Timestamp, churn_windows: Sequence[int]) -> dict[str, Any]:
    ordered = customer_invoices.sort_values("InvoiceDate").reset_index(drop=True)
    invoice_dates = pd.to_datetime(ordered["InvoiceDate"], errors="coerce").dropna()
    invoice_dates = pd.Series(invoice_dates).sort_values().reset_index(drop=True)
    first_purchase = pd.Timestamp(invoice_dates.iloc[0])
    last_purchase = pd.Timestamp(invoice_dates.iloc[-1])
    invoice_count = int(ordered["InvoiceNo"].nunique())
    transaction_count = int(len(ordered))
    total_revenue = float(ordered["Revenue"].sum())
    total_quantity = float(ordered["Quantity"].sum())
    unique_categories = int(ordered["ProductCategory"].nunique())
    unique_products = int(ordered["Description"].nunique())
    unique_countries = int(ordered["Country"].nunique())
    basket_sizes = ordered["BasketSize"].astype(float)
    gaps = invoice_dates.diff().dt.days.dropna().astype(float)
    average_gap = float(gaps.mean()) if not gaps.empty else float((snapshot_date - last_purchase).days)
    gap_std = float(gaps.std(ddof=0)) if len(gaps) > 1 else 0.0
    recency_trend = 0.0
    if len(gaps) >= 4:
        recent_gap_mean = float(gaps.tail(min(3, len(gaps))).mean())
        early_gap_mean = float(gaps.head(min(3, len(gaps))).mean())
        recency_trend = safe_change(recent_gap_mean, early_gap_mean)

    monthly_revenue, monthly_orders = _customer_monthly_series(ordered)
    quarterly = (
        ordered.assign(QuarterPeriod=ordered["InvoiceDate"].dt.to_period("Q"))
        .groupby("QuarterPeriod", as_index=False)
        .agg(QuarterRevenue=("Revenue", "sum"))
        .sort_values("QuarterPeriod")
    )
    monthly_revenue_series = pd.Series(monthly_revenue, dtype=float)
    monthly_orders_series = pd.Series(monthly_orders, dtype=float)

    revenue_trend = safe_trend(monthly_revenue_series.tolist())
    frequency_trend = safe_trend(monthly_orders_series.tolist())
    revenue_variability = float(monthly_revenue_series.std(ddof=0)) if len(monthly_revenue_series) > 1 else 0.0
    frequency_variability = float(monthly_orders_series.std(ddof=0)) if len(monthly_orders_series) > 1 else 0.0

    recent_90_revenue = _compute_window_metrics(ordered, snapshot_date, 90)
    recent_180_revenue = _compute_window_metrics(ordered, snapshot_date, 180)

    rolling_metrics: dict[str, float] = {}
    for window_days in churn_windows:
        rolling_metrics.update(_compute_window_metrics(ordered, snapshot_date, window_days))

    preferred_month = int(mode_or_default(ordered["InvoiceDate"].dt.month, int(last_purchase.month)))
    preferred_weekday = int(mode_or_default(ordered["InvoiceDate"].dt.dayofweek, int(last_purchase.dayofweek)))
    preferred_hour = int(mode_or_default(ordered["InvoiceDate"].dt.hour, int(last_purchase.hour)))
    repeat_purchase_ratio = safe_divide(max(invoice_count - 1, 0), max(invoice_count, 1), 0.0)
    average_interpurchase_time = float(gaps.mean()) if not gaps.empty else float((snapshot_date - last_purchase).days)
    customer_tenure = int((last_purchase - first_purchase).days + 1)
    retention_age = int((snapshot_date - first_purchase).days + 1)
    days_since_last_purchase = int((snapshot_date - last_purchase).days)
    average_order_value = safe_divide(total_revenue, invoice_count, 0.0)
    monthly_spend = float(monthly_revenue_series.mean()) if not monthly_revenue_series.empty else total_revenue
    quarterly_spend = float(quarterly["QuarterRevenue"].mean()) if not quarterly.empty else total_revenue
    annual_spend = total_revenue
    customer_velocity = safe_divide(invoice_count, max(customer_tenure, 1), 0.0)
    purchase_momentum = safe_change(recent_90_revenue["RollingRevenue_90"], recent_180_revenue["RollingRevenue_180"])
    purchase_variability = safe_divide(gap_std, average_gap, 0.0)
    recent_revenue_share = safe_divide(recent_90_revenue["RollingRevenue_90"], total_revenue, 0.0)
    revenue_concentration = 0.0
    if not monthly_revenue_series.empty and float(monthly_revenue_series.sum()) > 0:
        shares = monthly_revenue_series / monthly_revenue_series.sum()
        revenue_concentration = float((shares.pow(2)).sum())

    recent_orders_90 = recent_90_revenue["RecentOrderCount_90"]
    previous_orders_90 = recent_90_revenue["PreviousOrderCount_90"]
    recent_revenue_90 = recent_90_revenue["RecentRevenue_90"]
    previous_revenue_90 = recent_90_revenue["PreviousRevenue_90"]

    customer_growth_rate = safe_change(recent_revenue_90, previous_revenue_90)

    row: dict[str, Any] = {
        "CustomerID": int(customer_id),
        "FirstPurchase": first_purchase,
        "LastPurchase": last_purchase,
        "SnapshotDate": snapshot_date,
        "InvoiceCount": invoice_count,
        "TransactionCount": transaction_count,
        "TotalRevenue": total_revenue,
        "TotalQuantity": total_quantity,
        "AverageOrderValue": average_order_value,
        "AverageBasketSize": float(basket_sizes.mean()) if not basket_sizes.empty else 0.0,
        "MedianBasketSize": float(basket_sizes.median()) if not basket_sizes.empty else 0.0,
        "CustomerTenure": customer_tenure,
        "RetentionAge": retention_age,
        "DaysSinceLastPurchase": days_since_last_purchase,
        "PurchaseGap": average_gap,
        "AverageInterpurchaseTime": average_gap,
        "PurchaseVariability": purchase_variability,
        "RevenueVariability": revenue_variability,
        "FrequencyVariability": frequency_variability,
        "MonthlySpend": monthly_spend,
        "QuarterlySpend": quarterly_spend,
        "AnnualSpend": annual_spend,
        "CustomerVelocity": customer_velocity,
        "PurchaseMomentum": purchase_momentum,
        "CustomerGrowthRate": customer_growth_rate,
        "CategoryDiversity": unique_categories,
        "ProductDiversity": unique_products,
        "CountryDiversity": unique_countries,
        "PreferredPurchaseMonth": preferred_month,
        "PreferredPurchaseWeekday": preferred_weekday,
        "PreferredPurchaseHour": preferred_hour,
        "RepeatPurchaseRatio": repeat_purchase_ratio,
        "RevenueConcentration": revenue_concentration,
        "RecencyTrend": recency_trend,
        "FrequencyTrend": frequency_trend,
        "RevenueTrend": revenue_trend,
        "RecentRevenueShare_90": recent_revenue_share,
        "RecentOrderCount_90": recent_orders_90,
        "PreviousOrderCount_90": previous_orders_90,
        "RecentRevenue_90": recent_revenue_90,
        "PreviousRevenue_90": previous_revenue_90,
        "DominantCountry": mode_or_default(ordered["Country"], "Unknown"),
        "DominantCategory": mode_or_default(ordered["ProductCategory"], "Other"),
        "DominantProduct": mode_or_default(ordered["Description"], "Unknown"),
    }
    row.update(rolling_metrics)
    for window_days in churn_windows:
        row[f"ChurnLabel_{window_days}"] = int(days_since_last_purchase >= window_days)
    return row


def build_churn_labels(
    df: pd.DataFrame,
    *,
    churn_windows: Sequence[int] = DEFAULT_CHURN_WINDOWS,
    primary_window: int = DEFAULT_PRIMARY_WINDOW,
) -> pd.DataFrame:
    data = df.copy()
    if "DaysSinceLastPurchase" not in data.columns:
        raise KeyError("DaysSinceLastPurchase is required for churn label generation")
    for window_days in churn_windows:
        data[f"ChurnLabel_{window_days}"] = (data["DaysSinceLastPurchase"] >= window_days).astype(int)
    if primary_window not in churn_windows:
        data[f"ChurnLabel_{primary_window}"] = (data["DaysSinceLastPurchase"] >= primary_window).astype(int)
    data["IsChurn"] = data[f"ChurnLabel_{primary_window}"].astype(int)
    return data


def build_customer_churn_frame(
    df: pd.DataFrame,
    *,
    churn_windows: Sequence[int] = DEFAULT_CHURN_WINDOWS,
    primary_window: int = DEFAULT_PRIMARY_WINDOW,
) -> pd.DataFrame:
    logger.info("Building customer churn frame")
    data = normalize_retail_frame(df)
    invoice_summary = _build_invoice_summary(data)
    if invoice_summary.empty:
        raise ValueError("No valid customer invoices were found for churn modeling")

    snapshot_date = pd.Timestamp(invoice_summary["InvoiceDate"].max()).normalize() + pd.Timedelta(days=1)
    rows = []
    for customer_id, group in invoice_summary.groupby("CustomerID", sort=False):
        rows.append(_customer_summary_row(int(customer_id), group, snapshot_date, churn_windows))

    customer_frame = pd.DataFrame(rows).sort_values(["TotalRevenue", "InvoiceCount"], ascending=False).reset_index(drop=True)
    customer_frame = build_churn_labels(customer_frame, churn_windows=churn_windows, primary_window=primary_window)

    recency_percentile = 1.0 - safe_percentile(customer_frame["DaysSinceLastPurchase"])
    frequency_percentile = safe_percentile(customer_frame["InvoiceCount"])
    revenue_percentile = safe_percentile(customer_frame["TotalRevenue"])
    velocity_percentile = safe_percentile(customer_frame["CustomerVelocity"])
    diversity_percentile = safe_percentile(customer_frame["ProductDiversity"] + customer_frame["CategoryDiversity"])
    engagement_percentile = safe_percentile(customer_frame["RepeatPurchaseRatio"])

    customer_frame["CustomerActivityScore"] = (
        100.0
        * (
            0.35 * recency_percentile
            + 0.30 * frequency_percentile
            + 0.35 * revenue_percentile
        )
    ).round(2)
    customer_frame["CustomerEngagementScore"] = (
        100.0
        * (
            0.25 * engagement_percentile
            + 0.25 * velocity_percentile
            + 0.25 * diversity_percentile
            + 0.25 * frequency_percentile
        )
    ).round(2)
    customer_frame["CustomerHealthScore_Heuristic"] = (
        100.0
        * (
            0.40 * recency_percentile
            + 0.20 * frequency_percentile
            + 0.20 * revenue_percentile
            + 0.20 * engagement_percentile
        )
    ).clip(0, 100).round(2)
    customer_frame["CustomerHealthScore"] = customer_frame["CustomerHealthScore_Heuristic"].copy()
    customer_frame["RetentionProbability_Heuristic"] = (
        1.0 - (customer_frame["IsChurn"].astype(float) * 0.8) - (safe_percentile(customer_frame["DaysSinceLastPurchase"]) * 0.2)
    ).clip(0, 1)
    customer_frame["ExpectedNextPurchase"] = customer_frame["LastPurchase"] + pd.to_timedelta(
        customer_frame["AverageInterpurchaseTime"].fillna(customer_frame["DaysSinceLastPurchase"]).clip(lower=1),
        unit="D",
    )
    customer_frame.attrs["snapshot_date"] = snapshot_date
    customer_frame.attrs["churn_windows"] = tuple(int(window_days) for window_days in churn_windows)
    customer_frame.attrs["primary_window"] = int(primary_window)
    return customer_frame


def _training_exclusions() -> set[str]:
    return {
        "CustomerID",
        "FirstPurchase",
        "LastPurchase",
        "SnapshotDate",
        "ExpectedNextPurchase",
        "DominantCountry",
        "DominantCategory",
        "DominantProduct",
        "IsChurn",
        "CustomerHealthScore",
        "CustomerHealthScore_Heuristic",
        "RetentionProbability_Heuristic",
        "RecommendedAction",
        "ActionReasoning",
        "RiskCategory",
        "HealthBand",
        "CustomerSegment",
        "ChurnProbability",
        "RetentionProbability",
        "NextPurchaseProbability",
        "ExpectedLifetimeValue",
        "PredictedChurn",
        "PredictedChurnLabel",
    }


def customer_model_catalog() -> dict[str, ChurnModelSpec]:
    return {
        "Logistic Regression": ChurnModelSpec(
            name="Logistic Regression",
            factory=lambda: classification_pipeline(
                LogisticRegression(max_iter=3000, class_weight="balanced", random_state=DEFAULT_RANDOM_STATE),
                scale=True,
            ),
            scale=True,
            random_grid={
                "classifier__C": [0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
                "classifier__class_weight": [None, "balanced"],
            },
            grid={
                "classifier__C": [0.1, 0.5, 1.0, 2.0],
                "classifier__class_weight": [None, "balanced"],
            },
        ),
        "Decision Tree": ChurnModelSpec(
            name="Decision Tree",
            factory=lambda: classification_pipeline(
                DecisionTreeClassifier(random_state=DEFAULT_RANDOM_STATE, class_weight="balanced"),
            ),
            random_grid={
                "classifier__max_depth": [3, 4, 5, 6, 8, None],
                "classifier__min_samples_leaf": [1, 2, 4, 8],
                "classifier__class_weight": [None, "balanced"],
            },
            grid={
                "classifier__max_depth": [4, 6, None],
                "classifier__min_samples_leaf": [1, 2, 4],
                "classifier__class_weight": [None, "balanced"],
            },
        ),
        "Random Forest": ChurnModelSpec(
            name="Random Forest",
            factory=lambda: classification_pipeline(
                RandomForestClassifier(
                    n_estimators=250,
                    max_depth=None,
                    min_samples_leaf=3,
                    class_weight="balanced",
                    random_state=DEFAULT_RANDOM_STATE,
                    n_jobs=1,
                )
            ),
            random_grid={
                "classifier__n_estimators": [150, 200, 250, 300],
                "classifier__max_depth": [None, 6, 10, 14],
                "classifier__min_samples_leaf": [1, 2, 3, 5],
                "classifier__class_weight": [None, "balanced"],
            },
            grid={
                "classifier__n_estimators": [200, 250, 300],
                "classifier__max_depth": [None, 10, 14],
                "classifier__min_samples_leaf": [2, 3, 5],
                "classifier__class_weight": [None, "balanced"],
            },
        ),
        "Extra Trees": ChurnModelSpec(
            name="Extra Trees",
            factory=lambda: classification_pipeline(
                ExtraTreesClassifier(
                    n_estimators=250,
                    max_depth=None,
                    min_samples_leaf=2,
                    class_weight="balanced",
                    random_state=DEFAULT_RANDOM_STATE,
                    n_jobs=1,
                )
            ),
            random_grid={
                "classifier__n_estimators": [150, 200, 250, 300],
                "classifier__max_depth": [None, 6, 10, 14],
                "classifier__min_samples_leaf": [1, 2, 3, 5],
                "classifier__class_weight": [None, "balanced"],
            },
            grid={
                "classifier__n_estimators": [200, 250, 300],
                "classifier__max_depth": [None, 10, 14],
                "classifier__min_samples_leaf": [1, 2, 3],
                "classifier__class_weight": [None, "balanced"],
            },
        ),
        "Gradient Boosting": ChurnModelSpec(
            name="Gradient Boosting",
            factory=lambda: classification_pipeline(
                GradientBoostingClassifier(random_state=DEFAULT_RANDOM_STATE),
            ),
            random_grid={
                "classifier__n_estimators": [100, 150, 200, 250],
                "classifier__learning_rate": [0.01, 0.03, 0.05, 0.1],
                "classifier__max_depth": [2, 3, 4],
            },
            grid={
                "classifier__n_estimators": [100, 150, 200],
                "classifier__learning_rate": [0.03, 0.05, 0.1],
                "classifier__max_depth": [2, 3, 4],
            },
        ),
        "AdaBoost": ChurnModelSpec(
            name="AdaBoost",
            factory=lambda: classification_pipeline(
                AdaBoostClassifier(random_state=DEFAULT_RANDOM_STATE),
            ),
            random_grid={
                "classifier__n_estimators": [50, 100, 150, 200],
                "classifier__learning_rate": [0.3, 0.5, 0.8, 1.0],
            },
            grid={
                "classifier__n_estimators": [100, 150, 200],
                "classifier__learning_rate": [0.5, 0.8, 1.0],
            },
        ),
        "Support Vector Machine": ChurnModelSpec(
            name="Support Vector Machine",
            factory=lambda: classification_pipeline(
                SVC(probability=True, class_weight="balanced", random_state=DEFAULT_RANDOM_STATE),
                scale=True,
            ),
            scale=True,
            random_grid={
                "classifier__C": [0.1, 0.5, 1.0, 2.0, 5.0],
                "classifier__kernel": ["rbf", "linear"],
                "classifier__gamma": ["scale", "auto"],
            },
            grid={
                "classifier__C": [0.5, 1.0, 2.0],
                "classifier__kernel": ["rbf", "linear"],
                "classifier__gamma": ["scale", "auto"],
            },
        ),
        "KNN": ChurnModelSpec(
            name="KNN",
            factory=lambda: classification_pipeline(KNeighborsClassifier(n_neighbors=3), scale=True),
            scale=True,
            random_grid={
                "classifier__n_neighbors": [3, 5, 7, 9, 11, 13],
                "classifier__weights": ["uniform", "distance"],
                "classifier__p": [1, 2],
            },
            grid={
                "classifier__n_neighbors": [5, 7, 9],
                "classifier__weights": ["uniform", "distance"],
                "classifier__p": [1, 2],
            },
        ),
        "Naive Bayes": ChurnModelSpec(
            name="Naive Bayes",
            factory=lambda: classification_pipeline(GaussianNB()),
        ),
        "MLP Neural Network": ChurnModelSpec(
            name="MLP Neural Network",
            factory=lambda: classification_pipeline(
                MLPClassifier(
                    hidden_layer_sizes=(64, 32),
                    alpha=0.001,
                    learning_rate_init=0.001,
                    max_iter=600,
                    early_stopping=True,
                    random_state=DEFAULT_RANDOM_STATE,
                ),
                scale=True,
            ),
            scale=True,
            random_grid={
                "classifier__hidden_layer_sizes": [(32,), (64,), (64, 32), (128, 64)],
                "classifier__alpha": [0.0001, 0.001, 0.005, 0.01],
            },
            grid={
                "classifier__hidden_layer_sizes": [(64,), (64, 32)],
                "classifier__alpha": [0.0001, 0.001, 0.005],
            },
        ),
        "XGBoost": ChurnModelSpec(
            name="XGBoost",
            factory=(
                lambda: classification_pipeline(
                    XGBClassifier(
                        n_estimators=200,
                        max_depth=4,
                        learning_rate=0.05,
                        subsample=0.9,
                        colsample_bytree=0.9,
                        eval_metric="logloss",
                        random_state=DEFAULT_RANDOM_STATE,
                        n_jobs=1,
                    )
                )
            )
            if XGBClassifier is not None
            else None,
            available=XGBClassifier is not None,
            reason_unavailable="xgboost is not installed",
        ),
        "LightGBM": ChurnModelSpec(
            name="LightGBM",
            factory=(
                lambda: classification_pipeline(
                    LGBMClassifier(
                        n_estimators=200,
                        learning_rate=0.05,
                        num_leaves=31,
                        class_weight="balanced",
                        random_state=DEFAULT_RANDOM_STATE,
                    )
                )
            )
            if LGBMClassifier is not None
            else None,
            available=LGBMClassifier is not None,
            reason_unavailable="lightgbm is not installed",
        ),
        "CatBoost": ChurnModelSpec(
            name="CatBoost",
            factory=(
                lambda: classification_pipeline(
                    CatBoostClassifier(
                        iterations=200,
                        depth=6,
                        learning_rate=0.05,
                        verbose=False,
                        random_seed=DEFAULT_RANDOM_STATE,
                    )
                )
            )
            if CatBoostClassifier is not None
            else None,
            available=CatBoostClassifier is not None,
            reason_unavailable="catboost is not installed",
        ),
    }


def _select_numeric_features(customer_frame: pd.DataFrame) -> list[str]:
    numeric_columns = customer_frame.select_dtypes(include=[np.number, "bool"]).columns.tolist()
    excluded = _training_exclusions()
    features = [
        column
        for column in numeric_columns
        if column not in excluded and not column.startswith("ChurnLabel_") and column not in {"ProbabilityBucket"}
    ]
    return features


def _safe_split(
    features: pd.DataFrame,
    target: pd.Series,
    *,
    test_size: float = 0.2,
    validation_size: float = 0.25,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    stratify_target = target if target.value_counts().min() >= 2 else None
    train_features, test_features, train_target, test_target = train_test_split(
        features,
        target,
        test_size=test_size,
        random_state=DEFAULT_RANDOM_STATE,
        stratify=stratify_target,
    )
    stratify_train = train_target if train_target.value_counts().min() >= 2 else None
    train_features, validation_features, train_target, validation_target = train_test_split(
        train_features,
        train_target,
        test_size=validation_size,
        random_state=DEFAULT_RANDOM_STATE,
        stratify=stratify_train,
    )
    return train_features, validation_features, test_features, train_target, validation_target, test_target


def _safe_probability(estimator: Any, features: pd.DataFrame) -> np.ndarray:
    if hasattr(estimator, "predict_proba"):
        probabilities = estimator.predict_proba(features)
        if probabilities.ndim == 2 and probabilities.shape[1] > 1:
            return probabilities[:, 1]
        return probabilities.ravel()
    if hasattr(estimator, "decision_function"):
        scores = estimator.decision_function(features)
        scores = np.asarray(scores, dtype=float)
        return 1.0 / (1.0 + np.exp(-scores))
    predictions = estimator.predict(features)
    return np.asarray(predictions, dtype=float)


def fit_probability_calibrator(validation_probabilities: np.ndarray, validation_target: pd.Series) -> Any | None:
    if validation_target.nunique() < 2:
        return None
    calibration_model = LogisticRegression(max_iter=1000, random_state=DEFAULT_RANDOM_STATE)
    calibration_model.fit(np.asarray(validation_probabilities, dtype=float).reshape(-1, 1), validation_target)
    return calibration_model


def apply_probability_calibrator(calibrator: Any | None, base_probabilities: np.ndarray) -> np.ndarray:
    probabilities = np.asarray(base_probabilities, dtype=float).reshape(-1, 1)
    if calibrator is None:
        return probabilities.ravel()
    if hasattr(calibrator, "predict_proba"):
        return calibrator.predict_proba(probabilities)[:, 1]
    return probabilities.ravel()


def _optimize_threshold(target: pd.Series, probabilities: np.ndarray) -> float:
    precision, recall, thresholds = precision_recall_curve(target, probabilities)
    if len(thresholds) == 0:
        return 0.5
    f1_scores = np.divide(
        2 * precision[:-1] * recall[:-1],
        precision[:-1] + recall[:-1] + 1e-9,
    )
    if np.isnan(f1_scores).all():
        return 0.5
    return float(thresholds[int(np.nanargmax(f1_scores))])


def _classification_metrics(target: pd.Series, probabilities: np.ndarray, threshold: float) -> dict[str, float]:
    predicted = (probabilities >= threshold).astype(int)
    metrics = {
        "accuracy": float(accuracy_score(target, predicted)),
        "precision": float(precision_score(target, predicted, zero_division=0)),
        "recall": float(recall_score(target, predicted, zero_division=0)),
        "f1": float(f1_score(target, predicted, zero_division=0)),
        "balanced_accuracy": float(balanced_accuracy_score(target, predicted)),
        "mcc": float(matthews_corrcoef(target, predicted)) if len(np.unique(target)) > 1 else 0.0,
    }
    try:
        metrics["roc_auc"] = float(roc_auc_score(target, probabilities))
    except Exception:
        metrics["roc_auc"] = float("nan")
    try:
        metrics["pr_auc"] = float(average_precision_score(target, probabilities))
    except Exception:
        metrics["pr_auc"] = float("nan")
    try:
        metrics["log_loss"] = float(log_loss(target, np.clip(probabilities, 1e-6, 1 - 1e-6)))
    except Exception:
        metrics["log_loss"] = float("nan")
    try:
        metrics["brier_score"] = float(brier_score_loss(target, probabilities))
    except Exception:
        metrics["brier_score"] = float("nan")
    return metrics


def _evaluate_pipeline(
    model_name: str,
    estimator: Pipeline,
    train_features: pd.DataFrame,
    validation_features: pd.DataFrame,
    train_target: pd.Series,
    validation_target: pd.Series,
) -> dict[str, Any]:
    estimator.fit(train_features, train_target)
    validation_probabilities = _safe_probability(estimator, validation_features)
    threshold = _optimize_threshold(validation_target, validation_probabilities)
    metrics = _classification_metrics(validation_target, validation_probabilities, threshold)
    metrics.update(
        {
            "model_name": model_name,
            "status": "evaluated",
            "threshold": threshold,
            "train_rows": int(len(train_features)),
            "validation_rows": int(len(validation_features)),
        }
    )
    return {
        "model_name": model_name,
        "estimator": estimator,
        "threshold": threshold,
        "metrics": metrics,
        "validation_probabilities": validation_probabilities,
    }


def _search_model(
    model_name: str,
    spec: ChurnModelSpec,
    train_features: pd.DataFrame,
    validation_features: pd.DataFrame,
    train_target: pd.Series,
    validation_target: pd.Series,
) -> tuple[pd.DataFrame, dict[str, Any], pd.DataFrame]:
    if spec.factory is None or not spec.available:
        return (
            pd.DataFrame(
                [
                    {
                        "model_name": model_name,
                        "status": "skipped",
                        "reason": spec.reason_unavailable or "unavailable",
                    }
                ]
            ),
            {
                "model_name": model_name,
                "status": "skipped",
                "reason": spec.reason_unavailable or "unavailable",
                "estimator": None,
                "threshold": 0.5,
                "metrics": {},
            },
            pd.DataFrame(),
        )

    try:
        baseline = _evaluate_pipeline(model_name, spec.factory(), train_features, validation_features, train_target, validation_target)
    except Exception as exc:
        return (
            pd.DataFrame(
                [
                    {
                        "model_name": model_name,
                        "status": "skipped",
                        "reason": str(exc),
                    }
                ]
            ),
            {
                "model_name": model_name,
                "status": "skipped",
                "reason": str(exc),
                "estimator": None,
                "threshold": 0.5,
                "metrics": {},
            },
            pd.DataFrame(),
        )
    metrics_rows = [baseline["metrics"]]
    best_payload = baseline
    tuning_rows: list[dict[str, Any]] = []

    if spec.random_grid:
        cv_splits = min(MODEL_SEARCH_CV_SPLITS, int(train_target.value_counts().min()))
        if cv_splits >= 2 and len(train_features) >= 20:
            try:
                randomized_search = RandomizedSearchCV(
                    estimator=spec.factory(),
                    param_distributions=spec.random_grid,
                    n_iter=min(MODEL_SEARCH_RANDOM_ITERATIONS, max(1, len(train_features))),
                    scoring="f1",
                    cv=StratifiedKFold(n_splits=cv_splits, shuffle=True, random_state=DEFAULT_RANDOM_STATE),
                    random_state=DEFAULT_RANDOM_STATE,
                    n_jobs=1,
                    refit=True,
                )
                randomized_search.fit(train_features, train_target)
                randomized_estimator = randomized_search.best_estimator_
                randomized_probabilities = _safe_probability(randomized_estimator, validation_features)
                randomized_threshold = _optimize_threshold(validation_target, randomized_probabilities)
                randomized_metrics = _classification_metrics(validation_target, randomized_probabilities, randomized_threshold)
                randomized_metrics.update(
                    {
                        "model_name": model_name,
                        "status": "tuned_randomized",
                        "threshold": randomized_threshold,
                        "train_rows": int(len(train_features)),
                        "validation_rows": int(len(validation_features)),
                        "best_params": json.dumps(randomized_search.best_params_, default=str),
                    }
                )
                metrics_rows.append(randomized_metrics)
                tuning_rows.append(
                    {
                        "model_name": model_name,
                        "search_strategy": "RandomizedSearchCV",
                        "best_score": float(randomized_search.best_score_),
                        "best_params": json.dumps(randomized_search.best_params_, default=str),
                    }
                )
                if randomized_metrics["f1"] >= best_payload["metrics"].get("f1", -1):
                    best_payload = {
                        "model_name": model_name,
                        "estimator": randomized_estimator,
                        "threshold": randomized_threshold,
                        "metrics": randomized_metrics,
                    }
            except Exception as exc:
                tuning_rows.append(
                    {
                        "model_name": model_name,
                        "search_strategy": "RandomizedSearchCV",
                        "best_score": float("nan"),
                        "best_params": json.dumps({"error": str(exc)}),
                    }
                )

    if spec.grid:
        cv_splits = min(MODEL_SEARCH_CV_SPLITS, int(train_target.value_counts().min()))
        if cv_splits >= 2 and len(train_features) >= 20:
            try:
                grid_search = GridSearchCV(
                    estimator=spec.factory(),
                    param_grid=spec.grid,
                    scoring="f1",
                    cv=StratifiedKFold(n_splits=cv_splits, shuffle=True, random_state=DEFAULT_RANDOM_STATE),
                    n_jobs=1,
                    refit=True,
                )
                grid_search.fit(train_features, train_target)
                grid_estimator = grid_search.best_estimator_
                grid_probabilities = _safe_probability(grid_estimator, validation_features)
                grid_threshold = _optimize_threshold(validation_target, grid_probabilities)
                grid_metrics = _classification_metrics(validation_target, grid_probabilities, grid_threshold)
                grid_metrics.update(
                    {
                        "model_name": model_name,
                        "status": "tuned_grid",
                        "threshold": grid_threshold,
                        "train_rows": int(len(train_features)),
                        "validation_rows": int(len(validation_features)),
                        "best_params": json.dumps(grid_search.best_params_, default=str),
                    }
                )
                metrics_rows.append(grid_metrics)
                tuning_rows.append(
                    {
                        "model_name": model_name,
                        "search_strategy": "GridSearchCV",
                        "best_score": float(grid_search.best_score_),
                        "best_params": json.dumps(grid_search.best_params_, default=str),
                    }
                )
                if grid_metrics["f1"] >= best_payload["metrics"].get("f1", -1):
                    best_payload = {
                        "model_name": model_name,
                        "estimator": grid_estimator,
                        "threshold": grid_threshold,
                        "metrics": grid_metrics,
                    }
            except Exception as exc:
                tuning_rows.append(
                    {
                        "model_name": model_name,
                        "search_strategy": "GridSearchCV",
                        "best_score": float("nan"),
                        "best_params": json.dumps({"error": str(exc)}),
                    }
                )

    leaderboard = pd.DataFrame(metrics_rows)
    tuning_summary = pd.DataFrame(tuning_rows)
    return leaderboard, best_payload, tuning_summary


def _classify_health_bands(score: pd.Series) -> pd.Series:
    bins = [-np.inf, 20, 40, 60, 80, np.inf]
    labels = ["Critical", "High Risk", "Moderate", "Healthy", "VIP"]
    return pd.cut(score, bins=bins, labels=labels).astype(str)


def _classify_risk(probabilities: pd.Series, health_score: pd.Series) -> pd.Series:
    conditions = [
        (probabilities >= 0.80) | (health_score <= 25),
        (probabilities >= 0.60) | (health_score <= 45),
        (probabilities >= 0.35) | (health_score <= 65),
    ]
    choices = ["Critical", "High", "Medium"]
    return pd.Series(np.select(conditions, choices, default="Low"), index=probabilities.index)


def _predict_next_purchase_probability(frame: pd.DataFrame) -> pd.Series:
    retention = 1.0 - frame["ChurnProbability"].fillna(0.0)
    engagement = normalize_probability(frame["CustomerEngagementScore"].fillna(0.0))
    activity = normalize_probability(frame["CustomerActivityScore"].fillna(0.0))
    return (0.5 * retention + 0.25 * engagement + 0.25 * activity).clip(0, 1)


def _expected_lifetime_value(frame: pd.DataFrame) -> pd.Series:
    tenure_factor = normalize_probability(frame["CustomerTenure"].fillna(0.0))
    revenue_factor = normalize_probability(frame["AnnualSpend"].fillna(0.0))
    retention_factor = frame["RetentionProbability"].fillna(0.0)
    repeat_factor = normalize_probability(frame["RepeatPurchaseRatio"].fillna(0.0))
    base_value = frame["AnnualSpend"].fillna(0.0)
    multiplier = 0.75 + (0.5 * retention_factor) + (0.25 * tenure_factor) + (0.25 * repeat_factor) + (0.25 * revenue_factor)
    return (base_value * multiplier).clip(lower=0)


def _recommend_action(row: pd.Series) -> tuple[str, str]:
    churn_probability = float(row["ChurnProbability"])
    health_score = float(row["CustomerHealthScore"])
    expected_ltv = float(row["ExpectedLifetimeValue"])
    engagement = float(row["CustomerEngagementScore"])
    retention_probability = float(row["RetentionProbability"])

    if churn_probability >= 0.80 and expected_ltv > 0:
        return (
            "VIP Retention",
            "High-value customer with acute churn risk requires white-glove retention handling.",
        )
    if churn_probability >= 0.75:
        return (
            "High Priority Follow-up",
            "The customer is at immediate churn risk and should be contacted quickly by the retention team.",
        )
    if churn_probability >= 0.60 and engagement < 0.45:
        return (
            "Offer Discount",
            "A price incentive can re-activate a customer who is showing weak engagement and moderate churn risk.",
        )
    if churn_probability >= 0.50:
        return (
            "Send Email Campaign",
            "Lifecycle messaging is the lowest-friction retention tactic for customers in the medium-risk band.",
        )
    if retention_probability >= 0.80 and health_score >= 75:
        return (
            "Upsell",
            "The customer is healthy and high-intent, so a targeted upsell can grow wallet share.",
        )
    if retention_probability >= 0.70 and engagement >= 0.55:
        return (
            "Cross Sell",
            "Engaged customers with broad category behavior are good candidates for cross-sell offers.",
        )
    if health_score >= 85:
        return (
            "VIP Retention",
            "This is a highly healthy customer worth protecting with premium treatment.",
        )
    return (
        "Do Nothing",
        "Current behavior looks stable, so the customer can remain on the default nurture journey.",
    )


def generate_customer_intelligence_outputs(
    customer_frame: pd.DataFrame,
    *,
    primary_window: int = DEFAULT_PRIMARY_WINDOW,
) -> dict[str, Any]:
    frame = customer_frame.copy()
    feature_columns = _select_numeric_features(frame)
    if not feature_columns:
        raise ValueError("No numeric features were found for customer intelligence scoring")

    model_features = frame[feature_columns].copy()
    trainable_target = frame["IsChurn"].astype(int)

    train_features, validation_features, test_features, train_target, validation_target, test_target = _safe_split(
        model_features,
        trainable_target,
    )

    catalog = customer_model_catalog()
    leaderboard_frames: list[pd.DataFrame] = []
    tuning_frames: list[pd.DataFrame] = []
    best_payload: dict[str, Any] | None = None
    all_candidate_payloads: list[dict[str, Any]] = []

    for model_name, spec in catalog.items():
        leaderboard, payload, tuning_summary = _search_model(
            model_name,
            spec,
            train_features,
            validation_features,
            train_target,
            validation_target,
        )
        if not leaderboard.empty:
            leaderboard_frames.append(leaderboard)
        if not tuning_summary.empty:
            tuning_frames.append(tuning_summary)
        if payload.get("estimator") is not None:
            all_candidate_payloads.append(payload)
            if best_payload is None or payload["metrics"].get("f1", -1) >= best_payload["metrics"].get("f1", -1):
                best_payload = payload

    if best_payload is None:
        dummy_estimator = classification_pipeline(DummyClassifier(strategy="most_frequent"))
        dummy_estimator.fit(train_features, train_target)
        validation_probabilities = _safe_probability(dummy_estimator, validation_features)
        threshold = 0.5
        metrics = _classification_metrics(validation_target, validation_probabilities, threshold)
        metrics.update(
            {
                "model_name": "Dummy Classifier",
                "status": "fallback",
                "threshold": threshold,
                "train_rows": int(len(train_features)),
                "validation_rows": int(len(validation_features)),
            }
        )
        best_payload = {"model_name": "Dummy Classifier", "estimator": dummy_estimator, "threshold": threshold, "metrics": metrics}
        leaderboard_frames.append(pd.DataFrame([metrics]))

    leaderboard = pd.concat(leaderboard_frames, ignore_index=True, sort=False)
    tuning_summary = pd.concat(tuning_frames, ignore_index=True, sort=False) if tuning_frames else pd.DataFrame()
    leaderboard = leaderboard.sort_values(["f1", "roc_auc", "balanced_accuracy"], ascending=False).reset_index(drop=True)

    best_model_name = str(best_payload["model_name"])
    best_estimator = best_payload["estimator"]
    best_threshold = float(best_payload["threshold"])
    best_metrics = best_payload["metrics"]

    if len(train_features) >= 20 and train_target.value_counts().min() >= 2:
        selected_feature_count = min(MAX_FEATURES_FOR_RFE, len(feature_columns))
        if selected_feature_count >= 2:
            rfe_pipeline = classification_pipeline(
                LogisticRegression(max_iter=3000, class_weight="balanced", random_state=DEFAULT_RANDOM_STATE),
                scale=True,
            )
            rfe = RFE(estimator=rfe_pipeline.named_steps["classifier"], n_features_to_select=selected_feature_count, step=1)
            scaled_features = StandardScaler().fit_transform(train_features.fillna(train_features.median(numeric_only=True)))
            rfe.fit(scaled_features, train_target)
            selected_features = [feature for feature, keep in zip(feature_columns, rfe.support_, strict=False) if keep]
        else:
            selected_features = feature_columns
    else:
        selected_features = feature_columns

    feature_selector = {
        "selected_features": selected_features,
        "all_features": feature_columns,
        "primary_window": primary_window,
    }

    final_pipeline = best_estimator
    final_pipeline.fit(train_features[selected_features], train_target)
    validation_base_probabilities = _safe_probability(final_pipeline, validation_features[selected_features])
    probability_calibrator = fit_probability_calibrator(validation_base_probabilities, validation_target)
    scorer_base_probabilities = _safe_probability(final_pipeline, model_features[selected_features])
    scorer_probabilities = apply_probability_calibrator(probability_calibrator, scorer_base_probabilities)
    threshold = best_threshold
    frame["ChurnProbability"] = np.asarray(scorer_probabilities, dtype=float).clip(0, 1)
    frame["RetentionProbability"] = (1.0 - frame["ChurnProbability"]).clip(0, 1)
    frame["PredictedChurn"] = (frame["ChurnProbability"] >= threshold).astype(int)
    frame["PredictedChurnLabel"] = frame["PredictedChurn"].map({0: "Retain", 1: "Churn"})
    frame["ProbabilityConfidence"] = np.abs(frame["ChurnProbability"] - 0.5) * 2.0
    frame["ExpectedLifetimeValue"] = _expected_lifetime_value(frame).round(2)
    frame["NextPurchaseProbability"] = _predict_next_purchase_probability(frame).round(4)
    frame["HealthBand"] = _classify_health_bands(frame["CustomerHealthScore"])
    frame["RiskCategory"] = _classify_risk(frame["ChurnProbability"], frame["CustomerHealthScore"])
    frame["CustomerSegment"] = np.select(
        [
            (frame["RiskCategory"] == "Critical") & (frame["CustomerHealthScore"] >= 70),
            (frame["RiskCategory"] == "Low") & (frame["CustomerHealthScore"] >= 80),
            frame["RiskCategory"] == "Low",
            frame["RiskCategory"] == "Medium",
        ],
        ["VIP At Risk", "Champions", "Loyal", "Needs Attention"],
        default="At Risk",
    )
    recommendations = frame.apply(_recommend_action, axis=1, result_type="expand")
    frame["RecommendedAction"] = recommendations[0]
    frame["ActionReasoning"] = recommendations[1]
    frame["RetentionProbability"] = (
        0.60 * frame["RetentionProbability"]
        + 0.20 * frame["NextPurchaseProbability"]
        + 0.20 * (frame["CustomerHealthScore"] / 100.0)
    ).clip(0, 1)
    frame["ChurnProbability"] = (1.0 - frame["RetentionProbability"]).clip(0, 1)
    frame["RiskScore"] = (frame["ChurnProbability"] * 100.0).round(2)
    frame["CustomerHealthScore"] = (
        0.5 * frame["CustomerHealthScore_Heuristic"] + 0.5 * ((1.0 - frame["ChurnProbability"]) * 100.0)
    ).clip(0, 100).round(2)
    frame["PredictedChurn"] = (frame["ChurnProbability"] >= threshold).astype(int)
    frame["PredictedChurnLabel"] = frame["PredictedChurn"].map({0: "Retain", 1: "Churn"})

    health_features = frame[selected_features].copy()
    health_target = frame["CustomerHealthScore"].astype(float)
    health_model = regression_pipeline(RandomForestRegressor(n_estimators=250, random_state=DEFAULT_RANDOM_STATE, n_jobs=1))
    if len(health_features) >= 20:
        health_model.fit(health_features, health_target)
        frame["CustomerHealthScore"] = np.clip(health_model.predict(health_features), 0, 100).round(2)
    else:
        health_model = regression_pipeline(DummyRegressor(strategy="mean"))
        health_model.fit(health_features, health_target)
        frame["CustomerHealthScore"] = np.clip(health_model.predict(health_features), 0, 100).round(2)
    frame["HealthBand"] = _classify_health_bands(frame["CustomerHealthScore"])
    frame["NextPurchaseProbability"] = _predict_next_purchase_probability(frame).round(4)
    frame["RetentionProbability"] = (
        0.60 * frame["RetentionProbability"]
        + 0.20 * frame["NextPurchaseProbability"]
        + 0.20 * (frame["CustomerHealthScore"] / 100.0)
    ).clip(0, 1)
    frame["ChurnProbability"] = (1.0 - frame["RetentionProbability"]).clip(0, 1)
    frame["ExpectedLifetimeValue"] = _expected_lifetime_value(frame).round(2)
    frame["RiskScore"] = (frame["ChurnProbability"] * 100.0).round(2)
    frame["RiskCategory"] = _classify_risk(frame["ChurnProbability"], frame["CustomerHealthScore"])
    frame["CustomerSegment"] = np.select(
        [
            (frame["RiskCategory"] == "Critical") & (frame["CustomerHealthScore"] >= 70),
            (frame["RiskCategory"] == "Low") & (frame["CustomerHealthScore"] >= 80),
            frame["RiskCategory"] == "Low",
            frame["RiskCategory"] == "Medium",
        ],
        ["VIP At Risk", "Champions", "Loyal", "Needs Attention"],
        default="At Risk",
    )
    recommendations = frame.apply(_recommend_action, axis=1, result_type="expand")
    frame["RecommendedAction"] = recommendations[0]
    frame["ActionReasoning"] = recommendations[1]
    frame["PredictedChurn"] = (frame["ChurnProbability"] >= threshold).astype(int)
    frame["PredictedChurnLabel"] = frame["PredictedChurn"].map({0: "Retain", 1: "Churn"})

    retention_funnel = build_retention_funnel(frame)
    churn_funnel = build_churn_funnel(frame)
    customer_risk_matrix = build_customer_risk_matrix(frame)
    customer_journey_metrics = build_customer_journey_metrics(frame)
    customer_decay_curve = build_customer_decay_curve(frame)
    customer_lifetime_distribution = build_customer_lifetime_distribution(frame)
    retention_cohorts = build_retention_cohorts(frame)
    monthly_retention = build_monthly_retention(frame)
    quarterly_retention = build_quarterly_retention(frame)

    feature_importance_df = build_feature_importance(best_estimator, selected_features, model_features[selected_features], trainable_target)
    permutation_df = build_permutation_importance(best_estimator, selected_features, model_features[selected_features], trainable_target)
    shap_df = build_shap_summary(feature_importance_df, permutation_df)
    lime_df = build_lime_summary(frame, selected_features, final_pipeline)

    frame.attrs["snapshot_date"] = customer_frame.attrs.get("snapshot_date")
    frame.attrs["churn_windows"] = customer_frame.attrs.get("churn_windows")
    frame.attrs["primary_window"] = customer_frame.attrs.get("primary_window")
    frame.attrs["best_model_name"] = best_model_name
    frame.attrs["best_threshold"] = best_threshold
    frame.attrs["best_model_object"] = final_pipeline
    frame.attrs["probability_calibrator_object"] = probability_calibrator
    frame.attrs["health_model_object"] = health_model
    frame.attrs["leaderboard"] = leaderboard
    frame.attrs["tuning_summary"] = tuning_summary
    frame.attrs["feature_importance_frame"] = feature_importance_df
    frame.attrs["permutation_importance_frame"] = permutation_df
    frame.attrs["shap_summary_frame"] = shap_df
    frame.attrs["lime_summary_frame"] = lime_df
    frame.attrs["retention_funnel"] = retention_funnel
    frame.attrs["churn_funnel"] = churn_funnel
    frame.attrs["customer_risk_matrix"] = customer_risk_matrix
    frame.attrs["customer_journey_metrics"] = customer_journey_metrics
    frame.attrs["customer_decay_curve"] = customer_decay_curve
    frame.attrs["customer_lifetime_distribution"] = customer_lifetime_distribution
    frame.attrs["retention_cohorts"] = retention_cohorts
    frame.attrs["monthly_retention"] = monthly_retention
    frame.attrs["quarterly_retention"] = quarterly_retention

    return {
        "customer_frame": frame,
        "leaderboard": leaderboard,
        "tuning_summary": tuning_summary,
        "best_model_name": best_model_name,
        "best_model": final_pipeline,
        "probability_calibrator": probability_calibrator,
        "best_threshold": threshold,
        "selected_features": selected_features,
        "feature_selector": feature_selector,
        "feature_importance": feature_importance_df,
        "permutation_importance": permutation_df,
        "shap_summary": shap_df,
        "lime_summary": lime_df,
        "health_model": health_model,
        "retention_funnel": retention_funnel,
        "churn_funnel": churn_funnel,
        "customer_risk_matrix": customer_risk_matrix,
        "customer_journey_metrics": customer_journey_metrics,
        "customer_decay_curve": customer_decay_curve,
        "customer_lifetime_distribution": customer_lifetime_distribution,
        "retention_cohorts": retention_cohorts,
        "monthly_retention": monthly_retention,
        "quarterly_retention": quarterly_retention,
        "test_split": {
            "train_features": train_features,
            "validation_features": validation_features,
            "test_features": test_features,
            "train_target": train_target,
            "validation_target": validation_target,
            "test_target": test_target,
        },
        "best_metrics": best_metrics,
        "all_candidate_payloads": all_candidate_payloads,
    }


def build_feature_importance(model: Any, feature_columns: Sequence[str], features: pd.DataFrame, target: pd.Series) -> pd.DataFrame:
    if hasattr(model, "feature_importances_"):
        importance = np.asarray(model.feature_importances_, dtype=float)
    elif hasattr(model, "named_steps") and "classifier" in model.named_steps and hasattr(model.named_steps["classifier"], "feature_importances_"):
        importance = np.asarray(model.named_steps["classifier"].feature_importances_, dtype=float)
    elif hasattr(model, "named_steps") and "classifier" in model.named_steps and hasattr(model.named_steps["classifier"], "coef_"):
        coefficients = np.asarray(model.named_steps["classifier"].coef_)
        importance = np.abs(coefficients).ravel()
    else:
        importance = np.zeros(len(feature_columns), dtype=float)
    if len(importance) != len(feature_columns):
        importance = np.resize(importance, len(feature_columns))
    feature_importance = pd.DataFrame(
        {
            "feature": list(feature_columns),
            "importance": importance,
        }
    ).sort_values("importance", ascending=False)
    total = float(feature_importance["importance"].sum())
    if total > 0:
        feature_importance["importance_percent"] = (feature_importance["importance"] / total * 100.0).round(2)
    else:
        feature_importance["importance_percent"] = 0.0
    return feature_importance.reset_index(drop=True)


def build_permutation_importance(model: Any, feature_columns: Sequence[str], features: pd.DataFrame, target: pd.Series) -> pd.DataFrame:
    if len(features) < 10 or target.nunique() < 2:
        return pd.DataFrame({"feature": list(feature_columns), "importance_mean": 0.0, "importance_std": 0.0})
    try:
        permutation = permutation_importance(
            model,
            features,
            target,
            n_repeats=5,
            random_state=DEFAULT_RANDOM_STATE,
            scoring="f1",
        )
        return (
            pd.DataFrame(
                {
                    "feature": list(feature_columns),
                    "importance_mean": permutation.importances_mean,
                    "importance_std": permutation.importances_std,
                }
            )
            .sort_values("importance_mean", ascending=False)
            .reset_index(drop=True)
        )
    except Exception:
        return pd.DataFrame({"feature": list(feature_columns), "importance_mean": 0.0, "importance_std": 0.0})


def build_shap_summary(feature_importance_df: pd.DataFrame, permutation_df: pd.DataFrame) -> pd.DataFrame:
    base = permutation_df.copy()
    if base.empty:
        base = feature_importance_df.copy()
        if "importance_mean" not in base.columns and "importance" in base.columns:
            base["importance_mean"] = base["importance"].astype(float)
    if base.empty:
        return pd.DataFrame(columns=["feature", "mean_abs_shap", "status"])
    if "importance_mean" not in base.columns:
        base["importance_mean"] = 0.0
    base["status"] = "proxy" if shap is None else "proxy_fallback"
    base["mean_abs_shap"] = base["importance_mean"].astype(float).abs()
    return base[["feature", "mean_abs_shap", "status"]].sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)


def build_lime_summary(frame: pd.DataFrame, feature_columns: Sequence[str], model: Any) -> pd.DataFrame:
    if LimeTabularExplainer is None or frame.empty:
        return pd.DataFrame(columns=["feature", "weight", "status"])
    try:
        explainer = LimeTabularExplainer(
            training_data=frame[list(feature_columns)].fillna(0).to_numpy(),
            feature_names=list(feature_columns),
            class_names=["Retain", "Churn"],
            discretize_continuous=True,
            random_state=DEFAULT_RANDOM_STATE,
        )
        instance = frame[list(feature_columns)].fillna(0).iloc[0].to_numpy()
        explanation = explainer.explain_instance(instance, model.predict_proba, num_features=min(10, len(feature_columns)))
        rows = [{"feature": feature, "weight": float(weight), "status": "available"} for feature, weight in explanation.as_list()]
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame(columns=["feature", "weight", "status"])


def build_retention_funnel(frame: pd.DataFrame) -> pd.DataFrame:
    thresholds = [0.90, 0.75, 0.60, 0.40]
    rows = []
    for threshold in thresholds:
        rows.append(
            {
                "Stage": f"Retention >= {int(threshold * 100)}%",
                "Customers": int((frame["RetentionProbability"] >= threshold).sum()),
                "AverageHealth": float(frame.loc[frame["RetentionProbability"] >= threshold, "CustomerHealthScore"].mean()) if not frame.empty else 0.0,
            }
        )
    return pd.DataFrame(rows)


def build_churn_funnel(frame: pd.DataFrame) -> pd.DataFrame:
    thresholds = [0.10, 0.25, 0.50, 0.75]
    rows = []
    for threshold in thresholds:
        rows.append(
            {
                "Stage": f"Churn >= {int(threshold * 100)}%",
                "Customers": int((frame["ChurnProbability"] >= threshold).sum()),
                "AverageRisk": float(frame.loc[frame["ChurnProbability"] >= threshold, "RiskScore"].mean()) if not frame.empty else 0.0,
            }
        )
    return pd.DataFrame(rows)


def build_customer_risk_matrix(frame: pd.DataFrame) -> pd.DataFrame:
    risk_matrix = (
        frame.groupby(["RiskCategory", "HealthBand"], as_index=False)
        .agg(Customers=("CustomerID", "nunique"), AverageChurn=("ChurnProbability", "mean"), AverageLTV=("ExpectedLifetimeValue", "mean"))
    )
    return risk_matrix.sort_values(["RiskCategory", "HealthBand"]).reset_index(drop=True)


def build_customer_journey_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    temp = frame.copy()
    temp["FirstPurchaseMonth"] = temp["FirstPurchase"].dt.to_period("M").astype(str)
    temp["LastPurchaseMonth"] = temp["LastPurchase"].dt.to_period("M").astype(str)
    journey = (
        temp.groupby("FirstPurchaseMonth", as_index=False)
        .agg(
            Customers=("CustomerID", "nunique"),
            AverageChurn=("ChurnProbability", "mean"),
            AverageRetention=("RetentionProbability", "mean"),
            AverageHealth=("CustomerHealthScore", "mean"),
            AverageLTV=("ExpectedLifetimeValue", "mean"),
        )
        .sort_values("FirstPurchaseMonth")
        .reset_index(drop=True)
    )
    journey["CumulativeCustomers"] = journey["Customers"].cumsum()
    return journey


def build_customer_decay_curve(frame: pd.DataFrame) -> pd.DataFrame:
    temp = frame.copy()
    temp["RecencyBucket"] = pd.cut(
        temp["DaysSinceLastPurchase"],
        bins=[-np.inf, 7, 14, 30, 60, 90, 180, np.inf],
        labels=["0-7", "8-14", "15-30", "31-60", "61-90", "91-180", "180+"],
    )
    decay = (
        temp.groupby("RecencyBucket", as_index=False)
        .agg(Customers=("CustomerID", "nunique"), AverageChurn=("ChurnProbability", "mean"), AverageRetention=("RetentionProbability", "mean"))
        .reset_index(drop=True)
    )
    return decay


def build_customer_lifetime_distribution(frame: pd.DataFrame) -> pd.DataFrame:
    temp = frame.copy()
    temp["TenureBucket"] = pd.cut(
        temp["CustomerTenure"],
        bins=[-np.inf, 30, 90, 180, 365, np.inf],
        labels=["0-30", "31-90", "91-180", "181-365", "365+"],
    )
    lifetime = (
        temp.groupby("TenureBucket", as_index=False)
        .agg(Customers=("CustomerID", "nunique"), AverageLTV=("ExpectedLifetimeValue", "mean"), AverageHealth=("CustomerHealthScore", "mean"))
        .reset_index(drop=True)
    )
    return lifetime


def build_retention_cohorts(frame: pd.DataFrame) -> pd.DataFrame:
    temp = frame.copy()
    temp["AcquisitionMonth"] = temp["FirstPurchase"].dt.to_period("M").astype(str)
    temp["RetentionMonth"] = temp["LastPurchase"].dt.to_period("M").astype(str)
    cohorts = (
        temp.pivot_table(
            index="AcquisitionMonth",
            columns="RetentionMonth",
            values="RetentionProbability",
            aggfunc="mean",
        )
        .fillna(0.0)
        .sort_index()
    )
    cohorts.index.name = "AcquisitionMonth"
    return cohorts.reset_index()


def build_monthly_retention(frame: pd.DataFrame) -> pd.DataFrame:
    temp = frame.copy()
    temp["PurchaseMonth"] = temp["LastPurchase"].dt.to_period("M").astype(str)
    monthly = (
        temp.groupby("PurchaseMonth", as_index=False)
        .agg(Customers=("CustomerID", "nunique"), AverageRetention=("RetentionProbability", "mean"), AverageHealth=("CustomerHealthScore", "mean"))
        .sort_values("PurchaseMonth")
        .reset_index(drop=True)
    )
    return monthly


def build_quarterly_retention(frame: pd.DataFrame) -> pd.DataFrame:
    temp = frame.copy()
    temp["PurchaseQuarter"] = temp["LastPurchase"].dt.to_period("Q").astype(str)
    quarterly = (
        temp.groupby("PurchaseQuarter", as_index=False)
        .agg(Customers=("CustomerID", "nunique"), AverageRetention=("RetentionProbability", "mean"), AverageHealth=("CustomerHealthScore", "mean"))
        .sort_values("PurchaseQuarter")
        .reset_index(drop=True)
    )
    return quarterly


def create_customer_visualizations(
    frame: pd.DataFrame,
    leaderboard: pd.DataFrame,
    feature_importance_df: pd.DataFrame,
    permutation_df: pd.DataFrame,
    shap_df: pd.DataFrame,
    lime_df: pd.DataFrame,
    retention_funnel: pd.DataFrame,
    churn_funnel: pd.DataFrame,
    customer_risk_matrix: pd.DataFrame,
    customer_journey_metrics: pd.DataFrame,
    customer_decay_curve: pd.DataFrame,
    customer_lifetime_distribution: pd.DataFrame,
    retention_cohorts: pd.DataFrame,
    monthly_retention: pd.DataFrame,
    quarterly_retention: pd.DataFrame,
    figures_dir: Path,
    *,
    target_visual_count: int = TARGET_VISUAL_COUNT,
    figure_dpi: int = 300,
) -> list[Path]:
    figures_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    def save(fig: plt.Figure, title: str) -> None:
        if len(paths) >= target_visual_count:
            plt.close(fig)
            return
        path = persist_figure(fig, figures_dir / f"{len(paths) + 1:02d}_{slugify(title)}.png", dpi=figure_dpi)
        paths.append(path)

    if "PredictedChurn" in frame.columns:
        y_true = frame["IsChurn"].astype(int)
        y_prob = frame["ChurnProbability"].astype(float)
        y_pred = frame["PredictedChurn"].astype(int)
        try:
            from sklearn.metrics import roc_curve

            fpr, tpr, _ = roc_curve(y_true, y_prob)
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.plot(fpr, tpr, label="ROC")
            ax.plot([0, 1], [0, 1], linestyle="--", color="gray")
            ax.set_title("ROC Curve")
            ax.set_xlabel("False Positive Rate")
            ax.set_ylabel("True Positive Rate")
            ax.legend()
            save(fig, "roc_curve")
        except Exception:
            pass
        if len(paths) >= target_visual_count:
            return paths

        try:
            precision, recall, _ = precision_recall_curve(y_true, y_prob)
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.plot(recall, precision, label="PR")
            ax.set_title("PR Curve")
            ax.set_xlabel("Recall")
            ax.set_ylabel("Precision")
            ax.legend()
            save(fig, "pr_curve")
        except Exception:
            pass
        if len(paths) >= target_visual_count:
            return paths

        cm = confusion_matrix(y_true, y_pred)
        fig, ax = plt.subplots(figsize=(5, 4))
        sns.heatmap(cm, annot=True, fmt=".0f", cmap="Blues", cbar=False, ax=ax)
        ax.set_title("Confusion Matrix")
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")
        save(fig, "confusion_matrix")
        if len(paths) >= target_visual_count:
            return paths

        bins = np.linspace(0, 1, 11)
        frame["ProbabilityBucket"] = pd.cut(frame["ChurnProbability"], bins=bins, include_lowest=True)
        bucketed = frame.groupby("ProbabilityBucket", observed=False).agg(ChurnRate=("IsChurn", "mean")).reset_index()
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(data=bucketed, x="ProbabilityBucket", y="ChurnRate", ax=ax, color="#4C78A8")
        ax.set_title("Probability Distribution Calibration")
        ax.tick_params(axis="x", rotation=45)
        save(fig, "probability_distribution_calibration")
        if len(paths) >= target_visual_count:
            return paths

        try:
            fraction_of_positives, mean_predicted_value = calibration_curve(y_true, y_prob, n_bins=min(10, max(2, len(frame))))
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.plot(mean_predicted_value, fraction_of_positives, marker="o", label="Model")
            ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Perfect calibration")
            ax.set_title("Calibration Curve")
            ax.set_xlabel("Mean Predicted Churn Probability")
            ax.set_ylabel("Observed Churn Rate")
            ax.legend()
            save(fig, "calibration_curve")
        except Exception:
            pass
        if len(paths) >= target_visual_count:
            return paths

        lift_frame = frame[["IsChurn", "ChurnProbability"]].sort_values("ChurnProbability", ascending=False).reset_index(drop=True)
        lift_frame["Decile"] = pd.qcut(lift_frame.index + 1, q=min(10, len(lift_frame)), labels=False, duplicates="drop") + 1
        lift_summary = (
            lift_frame.groupby("Decile", as_index=False)
            .agg(Customers=("IsChurn", "size"), Churners=("IsChurn", "sum"), AverageProbability=("ChurnProbability", "mean"))
            .sort_values("Decile")
        )
        baseline_rate = max(float(lift_frame["IsChurn"].mean()), 1e-9)
        lift_summary["Lift"] = (lift_summary["Churners"] / lift_summary["Customers"]) / baseline_rate
        lift_summary["CumulativeGain"] = lift_summary["Churners"].cumsum() / max(float(lift_summary["Churners"].sum()), 1.0)

        fig, ax = plt.subplots(figsize=(8, 5))
        sns.lineplot(data=lift_summary, x="Decile", y="Lift", marker="o", ax=ax)
        ax.axhline(1.0, linestyle="--", color="gray")
        ax.set_title("Lift Chart")
        save(fig, "lift_chart")
        if len(paths) >= target_visual_count:
            return paths

        fig, ax = plt.subplots(figsize=(8, 5))
        sns.lineplot(data=lift_summary, x="Decile", y="CumulativeGain", marker="o", ax=ax)
        ax.plot(lift_summary["Decile"], lift_summary["Decile"] / max(float(lift_summary["Decile"].max()), 1.0), linestyle="--", color="gray")
        ax.set_title("Gain Chart")
        ax.set_ylabel("Cumulative Churn Capture")
        save(fig, "gain_chart")
        if len(paths) >= target_visual_count:
            return paths

    chart_specs = [
        ("Churn Probability Distribution", frame["ChurnProbability"], "#D62728"),
        ("Retention Probability Distribution", frame["RetentionProbability"], "#2CA02C"),
        ("Health Score Distribution", frame["CustomerHealthScore"], "#4C78A8"),
        ("Expected Lifetime Value Distribution", frame["ExpectedLifetimeValue"], "#F58518"),
        ("Days Since Last Purchase", frame["DaysSinceLastPurchase"], "#B279A2"),
        ("Purchase Gap Distribution", frame["PurchaseGap"], "#72B7B2"),
        ("Monthly Spend Distribution", frame["MonthlySpend"], "#E45756"),
        ("Quarterly Spend Distribution", frame["QuarterlySpend"], "#54A24B"),
        ("Annual Spend Distribution", frame["AnnualSpend"], "#9D755D"),
        ("Customer Velocity Distribution", frame["CustomerVelocity"], "#FF9DA6"),
        ("Customer Activity Score Distribution", frame["CustomerActivityScore"], "#EDC948"),
        ("Customer Engagement Score Distribution", frame["CustomerEngagementScore"], "#59A14F"),
        ("Revenue Concentration Distribution", frame["RevenueConcentration"], "#BAB0AC"),
        ("Repeat Purchase Ratio Distribution", frame["RepeatPurchaseRatio"], "#76B7B2"),
        ("Customer Growth Rate Distribution", frame["CustomerGrowthRate"], "#4E79A7"),
        ("Purchase Momentum Distribution", frame["PurchaseMomentum"], "#F28E2B"),
        ("Recency Trend Distribution", frame["RecencyTrend"], "#E15759"),
        ("Frequency Trend Distribution", frame["FrequencyTrend"], "#76B7B2"),
        ("Revenue Trend Distribution", frame["RevenueTrend"], "#59A14F"),
    ]
    for title, series, color in chart_specs:
        if series is None or series.empty:
            continue
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.histplot(series.fillna(0), bins=25, kde=True, ax=ax, color=color)
        ax.set_title(title)
        save(fig, title)
        if len(paths) >= target_visual_count:
            return paths

    risk_counts = frame["RiskCategory"].value_counts().reindex(["Critical", "High", "Medium", "Low"]).fillna(0)
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(x=risk_counts.index, y=risk_counts.values, ax=ax, palette="rocket")
    ax.set_title("Risk Category Distribution")
    save(fig, "risk_category_distribution")
    if len(paths) >= target_visual_count:
        return paths

    action_counts = frame["RecommendedAction"].value_counts().head(10)
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(x=action_counts.index, y=action_counts.values, ax=ax, palette="viridis")
    ax.set_title("Recommended Actions")
    ax.tick_params(axis="x", rotation=30)
    save(fig, "recommended_actions")
    if len(paths) >= target_visual_count:
        return paths

    health_counts = frame["HealthBand"].value_counts().reindex(["Critical", "High Risk", "Moderate", "Healthy", "VIP"]).fillna(0)
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(x=health_counts.index, y=health_counts.values, ax=ax, palette="mako")
    ax.set_title("Health Band Distribution")
    ax.tick_params(axis="x", rotation=30)
    save(fig, "health_band_distribution")
    if len(paths) >= target_visual_count:
        return paths

    if not leaderboard.empty:
        metric_columns = [column for column in ["f1", "roc_auc", "pr_auc", "balanced_accuracy"] if column in leaderboard.columns]
        for metric in metric_columns:
            ranked = leaderboard.sort_values(metric, ascending=False)
            fig, ax = plt.subplots(figsize=(10, 5))
            sns.barplot(data=ranked.head(10), x="model_name", y=metric, ax=ax, palette="crest")
            ax.set_title(f"Model Leaderboard - {metric.upper()}")
            ax.tick_params(axis="x", rotation=30)
            save(fig, f"model_leaderboard_{metric}")
            if len(paths) >= target_visual_count:
                return paths

    if not feature_importance_df.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(data=feature_importance_df.head(15), x="importance_percent", y="feature", ax=ax, palette="viridis")
        ax.set_title("Feature Importance")
        save(fig, "feature_importance")
        if len(paths) >= target_visual_count:
            return paths

    if not permutation_df.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(data=permutation_df.head(15), x="importance_mean", y="feature", ax=ax, palette="flare")
        ax.set_title("Permutation Importance")
        save(fig, "permutation_importance")
        if len(paths) >= target_visual_count:
            return paths

    if not shap_df.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(data=shap_df.head(15), x="mean_abs_shap", y="feature", ax=ax, palette="magma")
        ax.set_title("SHAP Summary Plot")
        save(fig, "shap_summary")
        if len(paths) >= target_visual_count:
            return paths

        waterfall_rows = shap_df.head(10).sort_values("mean_abs_shap", ascending=True)
        fig, ax = plt.subplots(figsize=(10, 5))
        draw_waterfall(
            ax,
            waterfall_rows["feature"].tolist(),
            waterfall_rows["mean_abs_shap"].astype(float).tolist(),
            "SHAP Waterfall Plot",
        )
        save(fig, "shap_waterfall_plot")
        if len(paths) >= target_visual_count:
            return paths

        top_shap_feature = str(shap_df.iloc[0]["feature"])
        if top_shap_feature in frame.columns:
            fig, ax = plt.subplots(figsize=(8, 5))
            sns.scatterplot(data=frame, x=top_shap_feature, y="ChurnProbability", hue="RiskCategory", ax=ax, s=40)
            ax.set_title(f"SHAP Dependence Plot - {top_shap_feature}")
            ax.tick_params(axis="x", rotation=30)
            save(fig, "shap_dependence_plot")
            if len(paths) >= target_visual_count:
                return paths

    if not lime_df.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(data=lime_df.head(10), x="weight", y="feature", ax=ax, palette="coolwarm")
        ax.set_title("LIME Explanation")
        save(fig, "lime_explanation")
        if len(paths) >= target_visual_count:
            return paths

    if not customer_risk_matrix.empty:
        pivot = customer_risk_matrix.pivot_table(index="RiskCategory", columns="HealthBand", values="Customers", fill_value=0)
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.heatmap(pivot, annot=True, fmt=".0f", cmap="YlGnBu", ax=ax)
        ax.set_title("Customer Risk Matrix")
        save(fig, "customer_risk_matrix")
        if len(paths) >= target_visual_count:
            return paths

    if not retention_funnel.empty:
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(data=retention_funnel, x="Stage", y="Customers", ax=ax, palette="Greens_r")
        ax.set_title("Retention Funnel")
        ax.tick_params(axis="x", rotation=30)
        save(fig, "retention_funnel")
        if len(paths) >= target_visual_count:
            return paths

    if not churn_funnel.empty:
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(data=churn_funnel, x="Stage", y="Customers", ax=ax, palette="Reds_r")
        ax.set_title("Churn Funnel")
        ax.tick_params(axis="x", rotation=30)
        save(fig, "churn_funnel")
        if len(paths) >= target_visual_count:
            return paths

    if not customer_decay_curve.empty:
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.lineplot(data=customer_decay_curve, x="RecencyBucket", y="AverageChurn", marker="o", ax=ax)
        ax.set_title("Customer Decay Curve")
        save(fig, "customer_decay_curve")
        if len(paths) >= target_visual_count:
            return paths

    if not customer_lifetime_distribution.empty:
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(data=customer_lifetime_distribution, x="TenureBucket", y="AverageLTV", ax=ax, palette="Blues")
        ax.set_title("Customer Lifetime Distribution")
        save(fig, "customer_lifetime_distribution")
        if len(paths) >= target_visual_count:
            return paths

    if not retention_cohorts.empty and retention_cohorts.shape[1] > 1:
        cohort_heatmap = retention_cohorts.set_index("AcquisitionMonth")
        fig, ax = plt.subplots(figsize=(12, 7))
        sns.heatmap(cohort_heatmap.drop(columns=[]), cmap="viridis", ax=ax)
        ax.set_title("Retention Cohorts")
        save(fig, "retention_cohorts")
        if len(paths) >= target_visual_count:
            return paths

    if not monthly_retention.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.lineplot(data=monthly_retention, x="PurchaseMonth", y="AverageRetention", marker="o", ax=ax)
        ax.set_title("Monthly Retention")
        ax.tick_params(axis="x", rotation=45)
        save(fig, "monthly_retention")
        if len(paths) >= target_visual_count:
            return paths

    if not quarterly_retention.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.lineplot(data=quarterly_retention, x="PurchaseQuarter", y="AverageRetention", marker="o", ax=ax)
        ax.set_title("Quarterly Retention")
        ax.tick_params(axis="x", rotation=45)
        save(fig, "quarterly_retention")
        if len(paths) >= target_visual_count:
            return paths

    if not frame.empty:
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        sns.histplot(frame["ChurnProbability"], bins=20, ax=axes[0, 0], color="#D62728")
        axes[0, 0].set_title("Executive Dashboard - Churn Risk")
        sns.histplot(frame["CustomerHealthScore"], bins=20, ax=axes[0, 1], color="#4C78A8")
        axes[0, 1].set_title("Executive Dashboard - Health")
        sns.barplot(data=frame["RecommendedAction"].value_counts().head(5).reset_index(), x="RecommendedAction", y="count", ax=axes[1, 0], color="#59A14F")
        axes[1, 0].set_title("Executive Dashboard - Actions")
        axes[1, 0].tick_params(axis="x", rotation=30)
        sns.scatterplot(data=frame, x="ChurnProbability", y="ExpectedLifetimeValue", hue="RiskCategory", ax=axes[1, 1], s=35)
        axes[1, 1].set_title("Executive Dashboard - Value at Risk")
        save(fig, "executive_dashboard_preview")
        if len(paths) >= target_visual_count:
            return paths

        customer_sample = frame.sort_values(["RiskScore", "ExpectedLifetimeValue"], ascending=False).head(20)
        fig, axes = plt.subplots(1, 3, figsize=(15, 4))
        sns.barplot(data=customer_sample, x="CustomerID", y="ChurnProbability", ax=axes[0], color="#E15759")
        axes[0].set_title("Customer Dashboard - Churn")
        axes[0].tick_params(axis="x", rotation=45)
        sns.barplot(data=customer_sample, x="CustomerID", y="CustomerHealthScore", ax=axes[1], color="#4E79A7")
        axes[1].set_title("Customer Dashboard - Health")
        axes[1].tick_params(axis="x", rotation=45)
        sns.barplot(data=customer_sample, x="CustomerID", y="ExpectedLifetimeValue", ax=axes[2], color="#F28E2B")
        axes[2].set_title("Customer Dashboard - LTV")
        axes[2].tick_params(axis="x", rotation=45)
        save(fig, "customer_dashboard_preview")
        if len(paths) >= target_visual_count:
            return paths

    if len(frame) >= 5:
        summary = frame.groupby("CustomerSegment", as_index=False).agg(
            ChurnProbability=("ChurnProbability", "mean"),
            RetentionProbability=("RetentionProbability", "mean"),
            Health=("CustomerHealthScore", "mean"),
            LTV=("ExpectedLifetimeValue", "mean"),
        )
        radar_labels = ["Churn", "Retention", "Health", "LTV"]
        normalized_ltv = normalize_probability(summary["LTV"]).fillna(0.0).reset_index(drop=True)
        for row in summary.itertuples(index=False):
            row_index = int(row.Index) if hasattr(row, "Index") else int(summary.index[summary["CustomerSegment"] == row.CustomerSegment][0])
            values = [
                float(getattr(row, "ChurnProbability")),
                float(getattr(row, "RetentionProbability")),
                float(getattr(row, "Health")) / 100.0,
                float(normalized_ltv.iloc[row_index]),
            ]
            fig = plt.figure(figsize=(6, 6))
            ax = fig.add_subplot(111, projection="polar")
            draw_radar_chart(ax, radar_labels, values, f"Radar - {row.CustomerSegment}")
            save(fig, f"radar_{row.CustomerSegment}")
            if len(paths) >= target_visual_count:
                return paths

    if not frame.empty:
        sample = frame.sort_values("ExpectedLifetimeValue", ascending=False).head(15)
        fig, ax = plt.subplots(figsize=(10, 4))
        draw_simple_treemap(ax, sample["ExpectedLifetimeValue"].tolist(), sample["CustomerSegment"].tolist(), "Lifetime Value Treemap")
        save(fig, "treemap_lifetime_value")
        if len(paths) >= target_visual_count:
            return paths

    if not frame.empty:
        sample = frame.sort_values("ExpectedLifetimeValue", ascending=False).head(20)
        fig, ax = plt.subplots(figsize=(8, 5))
        scatter = ax.scatter(
            sample["ChurnProbability"],
            sample["ExpectedLifetimeValue"],
            s=np.clip(sample["CustomerHealthScore"], 10, 300),
            c=sample["RiskScore"],
            cmap="coolwarm",
            alpha=0.75,
        )
        ax.set_title("Bubble Chart - Churn vs Lifetime Value")
        ax.set_xlabel("Churn Probability")
        ax.set_ylabel("Expected Lifetime Value")
        fig.colorbar(scatter, ax=ax, label="Risk Score")
        save(fig, "bubble_churn_ltv")
        if len(paths) >= target_visual_count:
            return paths

    if len(frame) >= 5:
        country_summary = (
            frame.groupby("DominantCountry", as_index=False)
            .agg(Customers=("CustomerID", "nunique"), AverageChurn=("ChurnProbability", "mean"), AverageLTV=("ExpectedLifetimeValue", "mean"))
            .sort_values("Customers", ascending=False)
        )
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(data=country_summary.head(12), x="DominantCountry", y="AverageChurn", ax=ax, palette="rocket")
        ax.set_title("Country Analysis")
        ax.tick_params(axis="x", rotation=45)
        save(fig, "country_analysis")
        if len(paths) >= target_visual_count:
            return paths

        category_summary = (
            frame.groupby("DominantCategory", as_index=False)
            .agg(Customers=("CustomerID", "nunique"), AverageChurn=("ChurnProbability", "mean"), AverageLTV=("ExpectedLifetimeValue", "mean"))
            .sort_values("Customers", ascending=False)
        )
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(data=category_summary.head(12), x="DominantCategory", y="AverageChurn", ax=ax, palette="mako")
        ax.set_title("Category Analysis")
        ax.tick_params(axis="x", rotation=45)
        save(fig, "category_analysis")
        if len(paths) >= target_visual_count:
            return paths

    if len(paths) < target_visual_count:
        additional_features = [
            "CustomerVelocity",
            "CustomerActivityScore",
            "CustomerEngagementScore",
            "CustomerHealthScore",
            "ExpectedLifetimeValue",
            "AnnualSpend",
            "MonthlySpend",
            "QuarterlySpend",
            "PurchaseGap",
            "AverageInterpurchaseTime",
            "RepeatPurchaseRatio",
            "RevenueConcentration",
            "RecentRevenueShare_90",
            "RecentOrderCount_90",
            "PreferredPurchaseHour",
            "PreferredPurchaseWeekday",
            "PreferredPurchaseMonth",
            "ProductDiversity",
            "CategoryDiversity",
            "CountryDiversity",
            "RecencyTrend",
            "FrequencyTrend",
            "RevenueTrend",
            "PurchaseMomentum",
            "CustomerGrowthRate",
        ]
        for feature_name in additional_features:
            if len(paths) >= target_visual_count or feature_name not in frame.columns:
                continue
            fig, ax = plt.subplots(figsize=(8, 5))
            sns.boxplot(data=frame, x="RiskCategory", y=feature_name, ax=ax, palette="Set2")
            ax.set_title(f"{feature_name} by Risk Category")
            ax.tick_params(axis="x", rotation=30)
            save(fig, f"{feature_name}_by_risk")

    if len(paths) < target_visual_count:
        scatter_pairs = [
            ("ChurnProbability", "CustomerHealthScore"),
            ("ChurnProbability", "ExpectedLifetimeValue"),
            ("RetentionProbability", "CustomerHealthScore"),
            ("CustomerActivityScore", "CustomerEngagementScore"),
            ("DaysSinceLastPurchase", "CustomerHealthScore"),
            ("CustomerVelocity", "ExpectedLifetimeValue"),
            ("RevenueTrend", "CustomerHealthScore"),
            ("PurchaseMomentum", "RetentionProbability"),
        ]
        for x_column, y_column in scatter_pairs:
            if len(paths) >= target_visual_count:
                break
            if x_column not in frame.columns or y_column not in frame.columns:
                continue
            fig, ax = plt.subplots(figsize=(8, 5))
            sns.scatterplot(data=frame, x=x_column, y=y_column, hue="RiskCategory", ax=ax, s=35, alpha=0.75)
            ax.set_title(f"{y_column} vs {x_column}")
            ax.tick_params(axis="x", rotation=30)
            save(fig, f"{x_column}_vs_{y_column}")

    return paths


def write_customer_reports(
    frame: pd.DataFrame,
    leaderboard: pd.DataFrame,
    tuning_summary: pd.DataFrame,
    feature_importance_df: pd.DataFrame,
    permutation_df: pd.DataFrame,
    shap_df: pd.DataFrame,
    lime_df: pd.DataFrame,
    retention_funnel: pd.DataFrame,
    churn_funnel: pd.DataFrame,
    customer_risk_matrix: pd.DataFrame,
    customer_journey_metrics: pd.DataFrame,
    customer_decay_curve: pd.DataFrame,
    customer_lifetime_distribution: pd.DataFrame,
    retention_cohorts: pd.DataFrame,
    monthly_retention: pd.DataFrame,
    quarterly_retention: pd.DataFrame,
    reports_dir: Path,
    figures_dir: Path,
) -> dict[str, Path]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    report_paths = {
        "customer_churn_report": reports_dir / "customer_churn_report.md",
        "customer_health_report": reports_dir / "customer_health_report.md",
        "executive_retention_report": reports_dir / "executive_retention_report.md",
        "business_action_report": reports_dir / "business_action_report.md",
        "model_comparison_report": reports_dir / "model_comparison_report.md",
    }

    feature_interpretation = customer_feature_descriptions()
    top_features = feature_importance_df.head(12)
    top_feature_lines = []
    for row in top_features.itertuples(index=False):
        feature_description = feature_interpretation.get(row.feature, "This feature contributes to churn and retention modeling.")
        top_feature_lines.append(f"- **{row.feature}**: {feature_description}")

    top_actions = frame.groupby("RecommendedAction", as_index=False).agg(Customers=("CustomerID", "nunique"), AverageChurn=("ChurnProbability", "mean"), AverageLTV=("ExpectedLifetimeValue", "mean")).sort_values("Customers", ascending=False)
    top_risk = frame.sort_values("ChurnProbability", ascending=False).head(15)
    top_health = frame.sort_values("CustomerHealthScore", ascending=False).head(15)
    top_actions_frame = frame[["CustomerID", "RecommendedAction", "ActionReasoning", "RiskCategory", "CustomerHealthScore", "ChurnProbability", "RetentionProbability", "ExpectedLifetimeValue"]].sort_values("ChurnProbability", ascending=False).head(20)

    write_text(
        f"""# Customer Churn Report

## Overview
RetailPulse Phase 5 builds a customer churn and retention intelligence layer on top of the curated transactional dataset. The workflow creates churn labels for 30, 60, 90, and 180 day windows, benchmarks a model zoo, calibrates probabilities, and assigns retention recommendations.

## Best Model
- Selected model: **{frame.attrs.get("best_model_name", "Unavailable")}**
- Threshold: **{frame.attrs.get("best_threshold", 0.5):.3f}**
- Customer rows: **{len(frame):,}**
- Churn rate: **{frame['IsChurn'].mean():.2%}**

## Model Leaderboard
{frame_to_markdown_like(leaderboard, rows=12)}

## Hyperparameter Tuning
{frame_to_markdown_like(tuning_summary, rows=12)}

## Important Feature Interpretation
{chr(10).join(top_feature_lines) if top_feature_lines else '- Feature importance was not available for this run.'}

## Probability and Risk Snapshot
{frame_to_markdown_like(frame[['CustomerID', 'ChurnProbability', 'RetentionProbability', 'RiskCategory', 'CustomerHealthScore']].head(12), rows=12)}

## Visual Assets
Generated figures are stored in `{figures_dir}`.
""",
        report_paths["customer_churn_report"],
    )

    write_text(
        f"""# Customer Health Report

## Health Score Distribution
Average health score: **{frame['CustomerHealthScore'].mean():.2f}**

Top health customers:
{frame_to_markdown_like(top_health[['CustomerID', 'CustomerHealthScore', 'ChurnProbability', 'RetentionProbability', 'ExpectedLifetimeValue']], rows=12)}

## Risk Relationship
{frame_to_markdown_like(customer_risk_matrix, rows=12)}

## Customer Journey Metrics
{frame_to_markdown_like(customer_journey_metrics, rows=12)}

## Monthly and Quarterly Retention
{frame_to_markdown_like(monthly_retention, rows=12)}

{frame_to_markdown_like(quarterly_retention, rows=12)}
""",
        report_paths["customer_health_report"],
    )

    write_text(
        f"""# Executive Retention Report

## Executive Summary
The retention engine identified {int((frame['RiskCategory'] == 'Critical').sum()):,} critical customers and {int((frame['RiskCategory'] == 'High').sum()):,} high-risk customers. The average retention probability is **{frame['RetentionProbability'].mean():.2%}** and the average expected lifetime value is **{frame['ExpectedLifetimeValue'].mean():,.2f}**.

## Key Retention Signals
- Highest risk cohorts are concentrated in the lowest recency buckets.
- Customers with strong activity and engagement scores are prime candidates for upsell and cross-sell actions.
- Retention funnels and decay curves are available in the visuals directory for leadership review.

## Funnel Snapshot
{frame_to_markdown_like(retention_funnel, rows=12)}

{frame_to_markdown_like(churn_funnel, rows=12)}

## Cohort Snapshot
{frame_to_markdown_like(retention_cohorts, rows=12)}
""",
        report_paths["executive_retention_report"],
    )

    write_text(
        f"""# Business Action Report

## Recommended Actions
{frame_to_markdown_like(top_actions_frame, rows=20)}

## Action Summary
{frame_to_markdown_like(top_actions, rows=20)}
""",
        report_paths["business_action_report"],
    )

    write_text(
        f"""# Model Comparison Report

## Leaderboard
{frame_to_markdown_like(leaderboard, rows=20)}

## Tuning Summary
{frame_to_markdown_like(tuning_summary, rows=20)}

## Explainability Tables
### Feature Importance
{frame_to_markdown_like(feature_importance_df, rows=15)}

### Permutation Importance
{frame_to_markdown_like(permutation_df, rows=15)}

### SHAP Summary
{frame_to_markdown_like(shap_df, rows=15)}

### LIME Summary
{frame_to_markdown_like(lime_df, rows=10)}
""",
        report_paths["model_comparison_report"],
    )
    return report_paths


def write_customer_churn_notebook(notebooks_dir: Path) -> Path:
    notebooks_dir.mkdir(parents=True, exist_ok=True)
    notebook_path = notebooks_dir / "06_customer_churn.ipynb"
    notebook = {
        "cells": [
            make_notebook_cell(
                "markdown",
                """
# RetailPulse Phase 5: Enterprise Customer Churn & Retention Intelligence

This notebook documents the churn intelligence workflow used to score customers, benchmark model candidates, generate explainability artifacts, and assign retention actions.

## Covered Topics

- Business problem framing
- Customer label generation
- Advanced feature engineering
- Model comparison and tuning
- Explainability and business interpretation
- Retention strategy recommendations
- Executive summary
                """,
            ),
            make_notebook_cell(
                "markdown",
                """
## Business Problem

RetailPulse needs a repeatable customer intelligence layer that can identify churn risk early enough to support retention actions, prioritization, and commercial uplift across the customer base.

The workflow creates labels from transactional history, scores churn probability, calibrates the probability surface, and converts the output into decision-ready retention recommendations.
                """,
            ),
            make_notebook_cell(
                "code",
                """
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path.cwd()
if PROJECT_ROOT.name == "notebooks":
    PROJECT_ROOT = PROJECT_ROOT.parent
if not (PROJECT_ROOT / "src").exists():
    raise FileNotFoundError("Run this notebook from the project root or the notebooks directory.")

sys.path.append(str(PROJECT_ROOT / "src"))

from customer_churn import run_phase_five
                """,
            ),
            make_notebook_cell(
                "code",
                """
result = run_phase_five(
    input_path=PROJECT_ROOT / "data" / "processed" / "final_processed_dataset.csv",
    output_dir=PROJECT_ROOT / "processed",
    reports_dir=PROJECT_ROOT / "reports",
    figures_dir=PROJECT_ROOT / "reports" / "figures",
    models_dir=PROJECT_ROOT / "models",
)

result["best_model_name"], len(result["visual_paths"])
                """,
            ),
            make_notebook_cell(
                "markdown",
                """
## Feature Engineering

The customer frame includes:

- Days since last purchase
- Purchase gaps and momentum
- Rolling revenue and purchase frequency
- Category, product, and country diversity
- Preferred month, weekday, and hour
- Activity, engagement, and health scores
- Lifetime value and recommendation columns
                """,
            ),
            make_notebook_cell(
                "code",
                """
customer_frame = result["customer_frame"]
customer_frame.head()
                """,
            ),
            make_notebook_cell(
                "markdown",
                """
## Model Comparison

The model zoo covers Logistic Regression, Decision Tree, Random Forest, Extra Trees, Gradient Boosting, AdaBoost, SVM, KNN, Naive Bayes, and MLP, plus optional XGBoost, LightGBM, and CatBoost when those libraries are installed.
                """,
            ),
            make_notebook_cell(
                "code",
                """
result["leaderboard"].sort_values(["f1", "roc_auc", "balanced_accuracy"], ascending=False)
                """,
            ),
            make_notebook_cell(
                "markdown",
                """
## Explainability

Use the feature importance, permutation importance, SHAP-style summary, and optional LIME frame to interpret why customers are labeled as high or low risk.
                """,
            ),
            make_notebook_cell(
                "code",
                """
result["feature_importance"].head(15)
                """,
            ),
            make_notebook_cell(
                "markdown",
                """
## Business Interpretation

- High churn probability with strong lifetime value should trigger VIP retention.
- Medium-risk, low-engagement customers respond well to discounts or email campaigns.
- Healthy customers with strong engagement are better cross-sell and upsell candidates.
                """,
            ),
            make_notebook_cell(
                "markdown",
                """
## Executive Summary

The Phase 5 workflow turns raw transaction history into a decision-ready customer intelligence package with customer scores, leadership reports, and 80+ visual diagnostics.
                """,
            ),
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    return write_notebook_json(notebook, notebook_path)


def save_customer_artifacts(
    frame: pd.DataFrame,
    leaderboard: pd.DataFrame,
    tuning_summary: pd.DataFrame,
    feature_importance_df: pd.DataFrame,
    permutation_df: pd.DataFrame,
    shap_df: pd.DataFrame,
    lime_df: pd.DataFrame,
    output_dir: Path,
    models_dir: Path,
    best_model: Any,
    health_model: Any,
    calibrator: Any,
    selected_features: Sequence[str],
    best_threshold: float,
    best_model_name: str,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)

    artifacts = {
        "customer_churn_predictions": output_dir / "customer_churn_predictions.csv",
        "customer_health_scores": output_dir / "customer_health_scores.csv",
        "customer_retention_metrics": output_dir / "customer_retention_metrics.csv",
        "customer_probability_scores": output_dir / "customer_probability_scores.csv",
        "customer_business_actions": output_dir / "customer_business_actions.csv",
        "customer_model_leaderboard": output_dir / "customer_model_leaderboard.csv",
        "best_churn_model": models_dir / "best_churn_model.pkl",
        "customer_health_model": models_dir / "customer_health_model.pkl",
        "probability_calibrator": models_dir / "probability_calibrator.pkl",
        "customer_pipeline": models_dir / "customer_pipeline.pkl",
        "customer_scaler": models_dir / "customer_scaler.pkl",
    }

    probability_frame = frame[
        [
            "CustomerID",
            "ChurnProbability",
            "RetentionProbability",
            "NextPurchaseProbability",
            "RiskCategory",
            "PredictedChurn",
            "PredictedChurnLabel",
            "RiskScore",
            "ProbabilityConfidence",
        ]
    ].copy()
    health_frame = frame[
        [
            "CustomerID",
            "CustomerHealthScore",
            "CustomerHealthScore_Heuristic",
            "HealthBand",
            "CustomerActivityScore",
            "CustomerEngagementScore",
            "RiskCategory",
        ]
    ].copy()
    retention_frame = frame.copy()
    action_frame = frame[
        [
            "CustomerID",
            "ChurnProbability",
            "RetentionProbability",
            "CustomerHealthScore",
            "ExpectedLifetimeValue",
            "RiskCategory",
            "RecommendedAction",
            "ActionReasoning",
            "CustomerSegment",
            "HealthBand",
        ]
    ].copy()

    write_dataframe(frame, artifacts["customer_churn_predictions"])
    write_dataframe(health_frame, artifacts["customer_health_scores"])
    write_dataframe(retention_frame, artifacts["customer_retention_metrics"])
    write_dataframe(probability_frame, artifacts["customer_probability_scores"])
    write_dataframe(action_frame, artifacts["customer_business_actions"])
    write_dataframe(leaderboard, artifacts["customer_model_leaderboard"])

    write_joblib(
        {
            "model_name": best_model_name,
            "threshold": best_threshold,
            "selected_features": list(selected_features),
            "estimator": best_model,
            "feature_importance": feature_importance_df.to_dict(orient="records"),
            "permutation_importance": permutation_df.to_dict(orient="records"),
            "shap_summary": shap_df.to_dict(orient="records"),
        },
        artifacts["best_churn_model"],
    )
    write_joblib(
        {
            "model_name": "Customer Health Model",
            "estimator": health_model,
            "feature_columns": list(selected_features),
        },
        artifacts["customer_health_model"],
    )
    write_joblib(calibrator, artifacts["probability_calibrator"])
    write_joblib(
        {
            "selected_features": list(selected_features),
            "best_model_name": best_model_name,
            "primary_target": "IsChurn",
            "threshold": best_threshold,
        },
        artifacts["customer_pipeline"],
    )
    write_joblib(
        {
            "status": "available",
            "model_name": best_model_name,
            "scaler": StandardScaler().fit(frame[list(selected_features)] if selected_features else frame.select_dtypes(include=[np.number])),
        },
        artifacts["customer_scaler"],
    )
    return artifacts


def run_phase_five(
    input_path: str | Path | None = None,
    *,
    input_df: pd.DataFrame | None = None,
    output_dir: str | Path | None = None,
    reports_dir: str | Path | None = None,
    figures_dir: str | Path | None = None,
    models_dir: str | Path | None = None,
    churn_windows: Sequence[int] = DEFAULT_CHURN_WINDOWS,
    primary_window: int = DEFAULT_PRIMARY_WINDOW,
    target_visual_count: int = TARGET_VISUAL_COUNT,
    figure_dpi: int = 300,
) -> dict[str, Any]:
    logger.info("Running RetailPulse Phase 5 churn and retention intelligence workflow")
    project_root = Path(__file__).resolve().parents[1]
    dataset_path = Path(input_path) if input_path is not None else FINAL_PROCESSED_DATA_PATH
    if input_df is not None:
        raw_df = input_df.copy()
    else:
        if not dataset_path.exists():
            raise FileNotFoundError(f"Processed dataset not found at {dataset_path}")
        raw_df = pd.read_csv(dataset_path, parse_dates=["InvoiceDate"])

    customer_frame = build_customer_churn_frame(raw_df, churn_windows=churn_windows, primary_window=primary_window)
    result = generate_customer_intelligence_outputs(customer_frame, primary_window=primary_window)
    scoring_output = result["customer_frame"].copy()
    leaderboard = result["leaderboard"]
    tuning_summary = result["tuning_summary"]
    best_model_name = result["best_model_name"]
    best_threshold = float(result["best_threshold"])
    best_model = result["best_model"]
    probability_calibrator = result["probability_calibrator"]
    health_model = result["health_model"]
    feature_importance_df = result["feature_importance"]
    permutation_df = result["permutation_importance"]
    shap_df = result["shap_summary"]
    lime_df = result["lime_summary"]
    retention_funnel = result["retention_funnel"]
    churn_funnel = result["churn_funnel"]
    customer_risk_matrix = result["customer_risk_matrix"]
    customer_journey_metrics = result["customer_journey_metrics"]
    customer_decay_curve = result["customer_decay_curve"]
    customer_lifetime_distribution = result["customer_lifetime_distribution"]
    retention_cohorts = result["retention_cohorts"]
    monthly_retention = result["monthly_retention"]
    quarterly_retention = result["quarterly_retention"]
    selected_features = result["selected_features"]

    scoring_output.attrs["best_model_name"] = best_model_name
    scoring_output.attrs["best_threshold"] = best_threshold
    scoring_output.attrs["leaderboard"] = leaderboard
    scoring_output.attrs["tuning_summary"] = tuning_summary
    scoring_output.attrs["feature_importance_frame"] = feature_importance_df
    scoring_output.attrs["permutation_importance_frame"] = permutation_df
    scoring_output.attrs["shap_summary_frame"] = shap_df
    scoring_output.attrs["lime_summary_frame"] = lime_df
    scoring_output.attrs["retention_funnel"] = retention_funnel
    scoring_output.attrs["churn_funnel"] = churn_funnel
    scoring_output.attrs["customer_risk_matrix"] = customer_risk_matrix
    scoring_output.attrs["customer_journey_metrics"] = customer_journey_metrics
    scoring_output.attrs["customer_decay_curve"] = customer_decay_curve
    scoring_output.attrs["customer_lifetime_distribution"] = customer_lifetime_distribution
    scoring_output.attrs["retention_cohorts"] = retention_cohorts
    scoring_output.attrs["monthly_retention"] = monthly_retention
    scoring_output.attrs["quarterly_retention"] = quarterly_retention
    scoring_output.attrs["best_model_object"] = best_model
    scoring_output.attrs["health_model_object"] = health_model

    feature_columns = list(selected_features)
    model_features = scoring_output[feature_columns].copy()

    output_path = Path(output_dir) if output_dir is not None else project_root / "processed"
    reports_path = Path(reports_dir) if reports_dir is not None else project_root / "reports"
    figures_path = Path(figures_dir) if figures_dir is not None else reports_path / "figures"
    models_path = Path(models_dir) if models_dir is not None else project_root / "models"
    output_path.mkdir(parents=True, exist_ok=True)
    reports_path.mkdir(parents=True, exist_ok=True)
    figures_path.mkdir(parents=True, exist_ok=True)
    models_path.mkdir(parents=True, exist_ok=True)
    visual_count = max(1, int(target_visual_count))

    visual_paths = create_customer_visualizations(
        scoring_output,
        leaderboard,
        feature_importance_df,
        permutation_df,
        shap_df,
        lime_df,
        retention_funnel,
        churn_funnel,
        customer_risk_matrix,
        customer_journey_metrics,
        customer_decay_curve,
        customer_lifetime_distribution,
        retention_cohorts,
        monthly_retention,
        quarterly_retention,
        figures_path,
        target_visual_count=visual_count,
        figure_dpi=figure_dpi,
    )

    report_paths = write_customer_reports(
        scoring_output,
        leaderboard,
        tuning_summary,
        feature_importance_df,
        permutation_df,
        shap_df,
        lime_df,
        retention_funnel,
        churn_funnel,
        customer_risk_matrix,
        customer_journey_metrics,
        customer_decay_curve,
        customer_lifetime_distribution,
        retention_cohorts,
        monthly_retention,
        quarterly_retention,
        reports_path,
        figures_path,
    )

    artifact_paths = save_customer_artifacts(
        scoring_output,
        leaderboard,
        tuning_summary,
        feature_importance_df,
        permutation_df,
        shap_df,
        lime_df,
        output_path,
        models_path,
        best_model,
        health_model,
        probability_calibrator,
        feature_columns,
        best_threshold,
        best_model_name,
    )

    notebook_path = write_customer_churn_notebook(project_root / "notebooks")

    try:
        from mlflow_utils import SafeMLflowRun, log_parameter, log_metric, log_artifact
        with SafeMLflowRun("RetailPulse Customer Churn", "customer_churn_run"):
            log_parameter("best_model_name", best_model_name)
            log_parameter("best_threshold", best_threshold)
            log_parameter("churn_windows", str(churn_windows))
            log_parameter("primary_window", primary_window)
            
            if leaderboard is not None and not leaderboard.empty:
                for _, row in leaderboard.iterrows():
                    m_name = f"{row.get('model', 'model')}_{row.get('configuration', 'default')}".replace(" ", "_")
                    log_metric(f"churn_{m_name}_accuracy", row.get("accuracy", 0.0))
                    log_metric(f"churn_{m_name}_precision", row.get("precision", 0.0))
                    log_metric(f"churn_{m_name}_recall", row.get("recall", 0.0))
                    log_metric(f"churn_{m_name}_f1", row.get("f1", 0.0))
                    log_metric(f"churn_{m_name}_roc_auc", row.get("roc_auc", 0.0))
                    
            for path in artifact_paths.values():
                log_artifact(path, "csv_outputs")
            for path in report_paths.values():
                log_artifact(path, "reports")
            for path in visual_paths:
                log_artifact(path, "plots")
            if notebook_path:
                log_artifact(notebook_path, "notebooks")
    except Exception as e:
        logger.warning(f"Failed to log Phase 5 churn run to MLflow: {e}")

    scoring_output["BestModel"] = best_model_name
    scoring_output["BestThreshold"] = best_threshold

    return {
        "customer_frame": scoring_output,
        "leaderboard": leaderboard,
        "tuning_summary": tuning_summary,
        "best_model_name": best_model_name,
        "best_threshold": best_threshold,
        "best_model": best_model,
        "probability_calibrator": probability_calibrator,
        "health_model": health_model,
        "feature_importance": feature_importance_df,
        "permutation_importance": permutation_df,
        "shap_summary": shap_df,
        "lime_summary": lime_df,
        "retention_funnel": retention_funnel,
        "churn_funnel": churn_funnel,
        "customer_risk_matrix": customer_risk_matrix,
        "customer_journey_metrics": customer_journey_metrics,
        "customer_decay_curve": customer_decay_curve,
        "customer_lifetime_distribution": customer_lifetime_distribution,
        "retention_cohorts": retention_cohorts,
        "monthly_retention": monthly_retention,
        "quarterly_retention": quarterly_retention,
        "artifact_paths": artifact_paths,
        "report_paths": report_paths,
        "visual_paths": visual_paths,
        "notebook_path": notebook_path,
    }


run_customer_churn = run_phase_five
