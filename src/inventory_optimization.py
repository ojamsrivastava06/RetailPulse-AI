from __future__ import annotations

import json
import math
import warnings
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from statistics import NormalDist
from typing import Any, Callable, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from chart_utils import draw_simple_treemap, draw_waterfall
from config import FINAL_PROCESSED_DATA_PATH
from constants import DEFAULT_FORECAST_HORIZONS, DEFAULT_RANDOM_STATE
from io_utils import backup_existing_file, slugify, write_dataframe, write_joblib, write_text
from logger import get_logger
from notebook_utils import make_notebook_cell, write_notebook_json
from report_utils import frame_to_markdown_like
from retail_rules import normalize_retail_frame

warnings.filterwarnings("ignore")
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


DEFAULT_HORIZONS = DEFAULT_FORECAST_HORIZONS
CARRYING_RATE = 0.22
EU_COUNTRIES = {
    "Austria",
    "Belgium",
    "Cyprus",
    "Czech Republic",
    "Denmark",
    "EIRE",
    "Finland",
    "France",
    "Germany",
    "Greece",
    "Iceland",
    "Italy",
    "Lithuania",
    "Malta",
    "Netherlands",
    "Norway",
    "Poland",
    "Portugal",
    "Spain",
    "Sweden",
    "Switzerland",
}


@dataclass(frozen=True)
class InventoryModelSpec:
    name: str
    available: bool
    factory: Callable[[], Pipeline] | None = None
    reason_unavailable: str | None = None


def clamp(value: float, lower: float, upper: float) -> float:
    return float(max(lower, min(upper, value)))


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    if denominator == 0:
        return float(default)
    return float(numerator / denominator)


def stable_fraction(key: str, salt: str = "") -> float:
    digest = sha256(f"{salt}|{key}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def score_to_level(score: float) -> str:
    if score >= 80:
        return "Critical"
    if score >= 60:
        return "High"
    if score >= 35:
        return "Medium"
    return "Low"


def classification_pipeline(estimator: Any, scale: bool = False) -> Pipeline:
    steps: list[tuple[str, Any]] = [("imputer", SimpleImputer(strategy="median"))]
    if scale:
        steps.append(("scaler", StandardScaler()))
    steps.append(("classifier", estimator))
    return Pipeline(steps)


def dependency_status_markdown() -> str:
    checks = {
        "xgboost": XGBClassifier is not None,
        "lightgbm": LGBMClassifier is not None,
        "catboost": CatBoostClassifier is not None,
    }
    return "\n".join(f"- {name}: {'available' if available else 'unavailable'}" for name, available in checks.items())


def inventory_model_catalog() -> dict[str, InventoryModelSpec]:
    return {
        "Logistic Regression": InventoryModelSpec(
            name="Logistic Regression",
            available=True,
            factory=lambda: classification_pipeline(
                LogisticRegression(max_iter=2000, class_weight="balanced", random_state=DEFAULT_RANDOM_STATE),
                scale=True,
            ),
        ),
        "Decision Tree": InventoryModelSpec(
            name="Decision Tree",
            available=True,
            factory=lambda: classification_pipeline(
                DecisionTreeClassifier(
                    max_depth=6,
                    min_samples_leaf=10,
                    class_weight="balanced",
                    random_state=DEFAULT_RANDOM_STATE,
                )
            ),
        ),
        "Random Forest": InventoryModelSpec(
            name="Random Forest",
            available=True,
            factory=lambda: classification_pipeline(
                RandomForestClassifier(
                    n_estimators=250,
                    max_depth=10,
                    min_samples_leaf=4,
                    class_weight="balanced",
                    random_state=DEFAULT_RANDOM_STATE,
                    n_jobs=-1,
                )
            ),
        ),
        "XGBoost": InventoryModelSpec(
            name="XGBoost",
            available=XGBClassifier is not None,
            factory=(
                lambda: classification_pipeline(
                    XGBClassifier(
                        n_estimators=250,
                        max_depth=5,
                        learning_rate=0.05,
                        subsample=0.9,
                        colsample_bytree=0.9,
                        eval_metric="logloss",
                        random_state=DEFAULT_RANDOM_STATE,
                        n_jobs=-1,
                    )
                )
            )
            if XGBClassifier is not None
            else None,
            reason_unavailable="xgboost is not installed",
        ),
        "LightGBM": InventoryModelSpec(
            name="LightGBM",
            available=LGBMClassifier is not None,
            factory=(
                lambda: classification_pipeline(
                    LGBMClassifier(
                        n_estimators=250,
                        learning_rate=0.05,
                        num_leaves=31,
                        class_weight="balanced",
                        random_state=DEFAULT_RANDOM_STATE,
                    )
                )
            )
            if LGBMClassifier is not None
            else None,
            reason_unavailable="lightgbm is not installed",
        ),
        "CatBoost": InventoryModelSpec(
            name="CatBoost",
            available=CatBoostClassifier is not None,
            factory=(
                lambda: classification_pipeline(
                    CatBoostClassifier(
                        iterations=250,
                        depth=6,
                        learning_rate=0.05,
                        verbose=False,
                        random_seed=DEFAULT_RANDOM_STATE,
                    )
                )
            )
            if CatBoostClassifier is not None
            else None,
            reason_unavailable="catboost is not installed",
        ),
    }


def assign_warehouse(country: str) -> str:
    if country == "United Kingdom":
        return "WH-UK-01"
    if country in EU_COUNTRIES:
        return "WH-EU-01"
    return "WH-INTL-01"


def load_inventory_sources(
    dataset_path: str | Path,
    forecast_path: str | Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw_df = pd.read_csv(dataset_path, parse_dates=["InvoiceDate"])
    forecast_df = pd.read_csv(forecast_path, parse_dates=["Date"])
    if "ForecastLevel" not in forecast_df.columns:
        raise KeyError("Forecast output is missing the ForecastLevel column.")
    sku_forecasts = forecast_df[forecast_df["ForecastLevel"] == "SKU"].copy()
    if sku_forecasts.empty:
        raise ValueError("Forecast output does not contain SKU-level predictions.")
    return raw_df, sku_forecasts


def build_inventory_history(raw_df: pd.DataFrame, sku_forecasts: pd.DataFrame) -> pd.DataFrame:
    normalized = normalize_retail_frame(raw_df)
    normalized["Date"] = normalized["InvoiceDate"].dt.normalize()
    selected = sku_forecasts[["SeriesKey", "Product", "Country", "ProductCategory"]].drop_duplicates().copy()

    daily = (
        normalized.groupby(["Date", "Description", "Country", "ProductCategory"], as_index=False)
        .agg(
            Sales=("Quantity", "sum"),
            Revenue=("Revenue", "sum"),
            Orders=("InvoiceNo", "nunique"),
            UniqueCustomers=("CustomerID", "nunique"),
            AverageUnitPrice=("Revenue", lambda series: float(series.sum())),
        )
        .sort_values(["Description", "Country", "ProductCategory", "Date"])
        .reset_index(drop=True)
    )
    daily["SeriesKey"] = (
        daily["Description"].astype(str)
        + " | "
        + daily["Country"].astype(str)
        + " | "
        + daily["ProductCategory"].astype(str)
    )
    daily["AverageUnitPrice"] = np.where(
        daily["Sales"] > 0,
        daily["Revenue"] / daily["Sales"],
        0.0,
    )

    frames: list[pd.DataFrame] = []
    end_date = pd.Timestamp(daily["Date"].max())
    for row in selected.itertuples(index=False):
        sparse = daily[daily["SeriesKey"] == row.SeriesKey].copy()
        if sparse.empty:
            continue
        date_index = pd.date_range(pd.Timestamp(sparse["Date"].min()), end_date, freq="D")
        completed = pd.DataFrame({"Date": date_index})
        completed = completed.merge(sparse, on="Date", how="left")
        completed["Description"] = completed["Description"].fillna(row.Product)
        completed["Country"] = completed["Country"].fillna(row.Country)
        completed["ProductCategory"] = completed["ProductCategory"].fillna(row.ProductCategory)
        completed["SeriesKey"] = row.SeriesKey
        for column in ["Sales", "Revenue", "Orders", "UniqueCustomers", "AverageUnitPrice"]:
            completed[column] = pd.to_numeric(completed[column], errors="coerce").fillna(0.0)
        frames.append(completed)

    if not frames:
        raise ValueError("No historical inventory series matched the forecast output.")
    return pd.concat(frames, ignore_index=True)


def compute_abc_xyz(history_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    summary_rows: list[dict[str, Any]] = []
    end_date = pd.Timestamp(history_df["Date"].max())

    for series_key, group in history_df.groupby("SeriesKey", sort=False):
        ordered = group.sort_values("Date").reset_index(drop=True)
        last_30 = ordered.tail(30)
        last_90 = ordered.tail(90)
        monthly = (
            ordered.assign(Month=ordered["Date"].dt.to_period("M").dt.to_timestamp())
            .groupby("Month", as_index=False)
            .agg(Sales=("Sales", "sum"), Revenue=("Revenue", "sum"))
        )
        monthly_mean = float(monthly["Sales"].mean()) if not monthly.empty else 0.0
        monthly_cv = safe_divide(float(monthly["Sales"].std(ddof=0)), monthly_mean, 0.0)
        peak_month_share = safe_divide(float(monthly["Sales"].max()), float(monthly["Sales"].sum()), 0.0) if not monthly.empty else 0.0

        total_sales = float(ordered["Sales"].sum())
        total_revenue = float(ordered["Revenue"].sum())
        daily_demand = float(last_30["Sales"].mean()) if not last_30.empty else float(ordered["Sales"].mean())
        weekly_demand = float(last_30["Sales"].tail(7).sum()) if len(last_30) >= 7 else float(last_30["Sales"].sum())
        monthly_demand = float(last_30["Sales"].sum())
        annual_demand = max(daily_demand * 365.0, monthly_demand * 12.0)
        demand_variability = float(last_90["Sales"].std(ddof=0)) if len(last_90) > 1 else 0.0
        demand_cv = safe_divide(demand_variability, daily_demand, 0.0)
        avg_unit_price = safe_divide(total_revenue, total_sales, 0.0)
        unit_cost = avg_unit_price * 0.65
        unit_margin = max(avg_unit_price - unit_cost, avg_unit_price * 0.2)

        lead_seed = stable_fraction(series_key, "lead_time")
        stock_seed = stable_fraction(series_key, "stock")
        supplier_seed = stable_fraction(series_key, "supplier")
        revenue_seed = stable_fraction(series_key, "revenue")

        lead_time = float(4 + round(lead_seed * 10))
        supplier_lead_time = float(lead_time + 1 + round(supplier_seed * 5))
        lead_time_variability = max(0.8, supplier_lead_time * (0.08 + demand_cv * 0.25))
        service_level = clamp(0.90 + (revenue_seed * 0.05) + min(demand_cv * 0.01, 0.02), 0.90, 0.99)
        z_score = NormalDist().inv_cdf(service_level)
        safety_stock = z_score * math.sqrt(max(supplier_lead_time, 1.0) * (demand_variability**2) + (daily_demand**2) * (lead_time_variability**2))
        reorder_point = (daily_demand * supplier_lead_time) + safety_stock
        ordering_cost = 45.0 + (math.log1p(max(monthly_demand, 1.0)) * 12.0) + (lead_seed * 25.0)
        eoq = math.sqrt(max((2.0 * max(annual_demand, 1.0) * ordering_cost) / max(unit_cost * CARRYING_RATE, 1.0), 1.0))
        current_stock = max(reorder_point + (daily_demand * (12.0 + supplier_lead_time + (stock_seed * 18.0))), eoq * 0.55)
        days_of_inventory = safe_divide(current_stock, daily_demand, 0.0)
        inventory_turnover = safe_divide(annual_demand, max(current_stock, 1.0), 0.0)
        stock_value = current_stock * unit_cost
        holding_cost = current_stock * unit_cost * CARRYING_RATE

        summary_rows.append(
            {
                "SeriesKey": series_key,
                "Product": ordered["Description"].iloc[0],
                "Country": ordered["Country"].iloc[0],
                "ProductCategory": ordered["ProductCategory"].iloc[0],
                "Warehouse": assign_warehouse(str(ordered["Country"].iloc[0])),
                "SupplierLane": f"SUP-{str(ordered['Country'].iloc[0])[:3].upper()}-{str(ordered['ProductCategory'].iloc[0])[:3].upper()}",
                "HistoryDays": int((end_date - pd.Timestamp(ordered["Date"].min())).days + 1),
                "TotalSales": total_sales,
                "TotalRevenue": total_revenue,
                "DailyDemand": daily_demand,
                "WeeklyDemand": weekly_demand,
                "MonthlyDemand": monthly_demand,
                "AnnualDemand": annual_demand,
                "DemandVariability": demand_variability,
                "DemandCV": demand_cv,
                "MonthlyDemandCV": monthly_cv,
                "PeakMonthShare": peak_month_share,
                "LeadTime": lead_time,
                "SupplierLeadTime": supplier_lead_time,
                "LeadTimeVariability": lead_time_variability,
                "ServiceLevel": service_level,
                "AverageUnitPrice": avg_unit_price,
                "UnitCost": unit_cost,
                "UnitMargin": unit_margin,
                "CurrentStockBase": current_stock,
                "HoldingCostBase": holding_cost,
                "OrderingCostBase": ordering_cost,
                "SafetyStockBase": safety_stock,
                "ReorderPointBase": reorder_point,
                "EconomicOrderQuantityBase": eoq,
                "InventoryTurnoverBase": inventory_turnover,
                "DaysOfInventoryBase": days_of_inventory,
                "StockValueBase": stock_value,
            }
        )

    summary = pd.DataFrame(summary_rows).sort_values("TotalRevenue", ascending=False).reset_index(drop=True)
    summary["RevenueShare"] = safe_divide(1.0, 1.0, 1.0)
    total_revenue_all = float(summary["TotalRevenue"].sum()) if not summary.empty else 0.0
    summary["RevenueShare"] = np.where(total_revenue_all > 0, summary["TotalRevenue"] / total_revenue_all, 0.0)
    summary["CumulativeRevenueShare"] = summary["RevenueShare"].cumsum()
    summary["ABCClass"] = np.where(
        summary["CumulativeRevenueShare"] <= 0.80,
        "A",
        np.where(summary["CumulativeRevenueShare"] <= 0.95, "B", "C"),
    )
    summary["XYZClass"] = pd.cut(
        summary["DemandCV"],
        bins=[-np.inf, 0.60, 1.10, np.inf],
        labels=["X", "Y", "Z"],
    ).astype(str)
    summary["ABCXYZMatrix"] = summary["ABCClass"] + "-" + summary["XYZClass"]

    summary["FastMovingItem"] = summary["InventoryTurnoverBase"] >= summary["InventoryTurnoverBase"].quantile(0.70)
    summary["SlowMovingItem"] = summary["InventoryTurnoverBase"] <= summary["InventoryTurnoverBase"].quantile(0.30)
    summary["DeadStockCandidate"] = (
        (summary["InventoryTurnoverBase"] <= summary["InventoryTurnoverBase"].quantile(0.20))
        & (summary["CurrentStockBase"] >= summary["CurrentStockBase"].median())
    )
    summary["SeasonalProduct"] = (summary["PeakMonthShare"] >= 0.20) | (summary["MonthlyDemandCV"] >= 0.80)
    summary["CriticalProduct"] = (summary["ABCClass"] == "A") | (summary["ServiceLevel"] >= 0.97) | (summary["SupplierLeadTime"] >= summary["SupplierLeadTime"].quantile(0.75))
    summary["HighValueItem"] = summary["StockValueBase"] >= summary["StockValueBase"].quantile(0.75)
    summary["LowValueItem"] = summary["StockValueBase"] <= summary["StockValueBase"].quantile(0.25)

    abc_analysis = summary[
        [
            "SeriesKey",
            "Product",
            "Country",
            "ProductCategory",
            "TotalRevenue",
            "RevenueShare",
            "CumulativeRevenueShare",
            "ABCClass",
            "HighValueItem",
            "CriticalProduct",
        ]
    ].copy()
    xyz_analysis = summary[
        [
            "SeriesKey",
            "Product",
            "Country",
            "ProductCategory",
            "DemandVariability",
            "DemandCV",
            "MonthlyDemandCV",
            "XYZClass",
            "FastMovingItem",
            "SlowMovingItem",
            "SeasonalProduct",
        ]
    ].copy()
    abc_xyz_matrix = (
        summary.groupby(["ABCClass", "XYZClass"], as_index=False)
        .agg(
            ItemCount=("SeriesKey", "nunique"),
            TotalRevenue=("TotalRevenue", "sum"),
            StockValue=("StockValueBase", "sum"),
        )
        .sort_values(["ABCClass", "XYZClass"])
        .reset_index(drop=True)
    )
    return summary, abc_analysis, xyz_analysis, abc_xyz_matrix


def simulate_inventory_dataset(summary_df: pd.DataFrame, sku_forecasts: pd.DataFrame) -> pd.DataFrame:
    meta = summary_df.set_index("SeriesKey")
    rows: list[dict[str, Any]] = []

    for (series_key, horizon_days), group in sku_forecasts.groupby(["SeriesKey", "HorizonDays"], sort=False):
        if series_key not in meta.index:
            continue
        static = meta.loc[series_key]
        ordered = group.sort_values("Date").reset_index(drop=True)
        opening_stock = float(static["CurrentStockBase"])
        pending_orders: list[tuple[pd.Timestamp, float]] = []

        for idx, row in ordered.iterrows():
            future_date = pd.Timestamp(row["Date"])
            inbound_receipts = sum(quantity for arrival, quantity in pending_orders if arrival <= future_date)
            pending_orders = [(arrival, quantity) for arrival, quantity in pending_orders if arrival > future_date]
            opening_stock = max(opening_stock + inbound_receipts, 0.0)
            forecast_demand = float(row["ForecastDemand"])
            forecast_revenue = float(row["ForecastRevenue"])
            lower_95 = float(row["Lower95Demand"])
            upper_95 = float(row["Upper95Demand"])
            unmet_demand = max(0.0, forecast_demand - opening_stock)
            estimated_stock = max(0.0, opening_stock - forecast_demand)

            lookahead_window = max(int(math.ceil(float(static["SupplierLeadTime"]))), 1)
            projected_lead_time_demand = float(
                ordered.iloc[idx : idx + lookahead_window]["ForecastDemand"].sum()
            )
            demand_buffer_units = max(0.0, upper_95 - forecast_demand)
            safety_stock = max(float(static["SafetyStockBase"]), demand_buffer_units + float(static["DemandVariability"]) * math.sqrt(max(float(static["SupplierLeadTime"]), 1.0)))
            reorder_point = (float(static["DailyDemand"]) * float(static["SupplierLeadTime"])) + safety_stock
            reorder_quantity = 0.0
            reorder_today = False
            if estimated_stock <= reorder_point:
                reorder_quantity = max(
                    float(static["EconomicOrderQuantityBase"]),
                    projected_lead_time_demand + safety_stock - estimated_stock,
                )
                if reorder_quantity > 0:
                    arrival_date = future_date + pd.Timedelta(days=int(math.ceil(float(static["SupplierLeadTime"]))))
                    pending_orders.append((arrival_date, reorder_quantity))
                    reorder_today = True

            pending_inbound_units = float(sum(quantity for _, quantity in pending_orders))
            daily_demand = float(static["DailyDemand"])
            stock_coverage_days = safe_divide(estimated_stock, daily_demand, 0.0)
            days_of_inventory = safe_divide(opening_stock, daily_demand, 0.0)
            stock_value = estimated_stock * float(static["UnitCost"])
            holding_cost = estimated_stock * float(static["UnitCost"]) * CARRYING_RATE / 365.0
            inventory_carrying_cost = opening_stock * float(static["UnitCost"]) * CARRYING_RATE / 365.0
            ordering_cost = float(static["OrderingCostBase"]) if reorder_today else 0.0
            stockout_cost = unmet_demand * float(static["UnitMargin"]) * 1.75
            total_inventory_cost = holding_cost + ordering_cost + stockout_cost
            optimized_lead_time = max(2.0, float(static["SupplierLeadTime"]) - min(float(static["LeadTimeVariability"]) * 0.30, 3.0))
            optimized_inventory_cost = total_inventory_cost * (0.88 if reorder_today or unmet_demand > 0 else 0.94)
            inventory_savings = max(0.0, total_inventory_cost - optimized_inventory_cost)
            potential_revenue_loss = unmet_demand * float(static["AverageUnitPrice"])
            expected_profit_improvement = inventory_savings + (potential_revenue_loss * 0.30)
            warehouse_allocation_score = clamp(
                100.0
                - abs(stock_coverage_days - (float(static["SupplierLeadTime"]) * 2.0)) * 1.2
                - max(0.0, unmet_demand * 0.08)
                + min(forecast_revenue / max(stock_value, 1.0), 20.0),
                0.0,
                100.0,
            )

            stockout_risk_score = clamp(
                safe_divide(reorder_point - estimated_stock, max(reorder_point, 1.0), 0.0) * 100.0
                + max(0.0, float(static["SupplierLeadTime"]) - stock_coverage_days) * 6.0
                + max(0.0, unmet_demand) * 0.15,
                0.0,
                100.0,
            )
            overstock_risk_score = clamp(
                safe_divide(estimated_stock - (float(static["MonthlyDemand"]) * 1.5), max(float(static["MonthlyDemand"]) * 1.5, 1.0), 0.0) * 100.0
                + max(0.0, stock_coverage_days - 75.0) * 0.8,
                0.0,
                100.0,
            )
            demand_spike_risk_score = clamp(
                safe_divide(upper_95 - forecast_demand, max(forecast_demand, 1.0), 0.0) * 100.0
                + safe_divide(forecast_demand - daily_demand, max(float(static["DemandVariability"]), 1.0), 0.0) * 8.0,
                0.0,
                100.0,
            )
            supplier_delay_risk_score = clamp(
                (float(static["SupplierLeadTime"]) * 3.2) + (float(static["LeadTimeVariability"]) * 7.5),
                0.0,
                100.0,
            )
            inventory_age_risk_score = clamp(
                max(0.0, stock_coverage_days - 60.0) * 1.2
                + (18.0 if bool(static["SlowMovingItem"]) else 0.0)
                + (28.0 if bool(static["DeadStockCandidate"]) else 0.0),
                0.0,
                100.0,
            )
            inventory_risk_score = clamp(
                (stockout_risk_score * 0.35)
                + (overstock_risk_score * 0.22)
                + (demand_spike_risk_score * 0.16)
                + (supplier_delay_risk_score * 0.17)
                + (inventory_age_risk_score * 0.10),
                0.0,
                100.0,
            )
            inventory_health_score = clamp(
                100.0
                - (inventory_risk_score * 0.72)
                + min(float(static["InventoryTurnoverBase"]) * 5.0, 18.0)
                + (float(static["ServiceLevel"]) * 12.0)
                - max(0.0, stock_coverage_days - 120.0) * 0.10,
                0.0,
                100.0,
            )

            rows.append(
                {
                    "Date": future_date,
                    "HorizonDays": int(horizon_days),
                    "SeriesKey": series_key,
                    "Product": static["Product"],
                    "Country": static["Country"],
                    "ProductCategory": static["ProductCategory"],
                    "Warehouse": static["Warehouse"],
                    "SupplierLane": static["SupplierLane"],
                    "ABCClass": static["ABCClass"],
                    "XYZClass": static["XYZClass"],
                    "ABCXYZMatrix": static["ABCXYZMatrix"],
                    "FastMovingItem": bool(static["FastMovingItem"]),
                    "SlowMovingItem": bool(static["SlowMovingItem"]),
                    "DeadStockCandidate": bool(static["DeadStockCandidate"]),
                    "SeasonalProduct": bool(static["SeasonalProduct"]),
                    "CriticalProduct": bool(static["CriticalProduct"]),
                    "HighValueItem": bool(static["HighValueItem"]),
                    "LowValueItem": bool(static["LowValueItem"]),
                    "CurrentStock": opening_stock,
                    "EstimatedStock": estimated_stock,
                    "ForecastDemand": forecast_demand,
                    "ForecastRevenue": forecast_revenue,
                    "Lower95Demand": lower_95,
                    "Upper95Demand": upper_95,
                    "DailyDemand": daily_demand,
                    "WeeklyDemand": float(static["WeeklyDemand"]),
                    "MonthlyDemand": float(static["MonthlyDemand"]),
                    "AnnualDemand": float(static["AnnualDemand"]),
                    "LeadTime": float(static["LeadTime"]),
                    "SupplierLeadTime": float(static["SupplierLeadTime"]),
                    "HoldingCost": holding_cost,
                    "OrderingCost": ordering_cost,
                    "InventoryCarryingCost": inventory_carrying_cost,
                    "StockValue": stock_value,
                    "SafetyStock": safety_stock,
                    "ReorderPoint": reorder_point,
                    "ReorderQuantity": reorder_quantity,
                    "EconomicOrderQuantity": float(static["EconomicOrderQuantityBase"]),
                    "InventoryTurnover": float(static["InventoryTurnoverBase"]),
                    "DaysOfInventory": days_of_inventory,
                    "ServiceLevel": float(static["ServiceLevel"]),
                    "StockCoverageDays": stock_coverage_days,
                    "DemandVariability": float(static["DemandVariability"]),
                    "LeadTimeVariability": float(static["LeadTimeVariability"]),
                    "DemandBufferUnits": demand_buffer_units,
                    "OptimizedLeadTime": optimized_lead_time,
                    "WarehouseAllocationScore": warehouse_allocation_score,
                    "StockoutRiskScore": stockout_risk_score,
                    "OverstockRiskScore": overstock_risk_score,
                    "DemandSpikeRiskScore": demand_spike_risk_score,
                    "SupplierDelayRiskScore": supplier_delay_risk_score,
                    "InventoryAgeRiskScore": inventory_age_risk_score,
                    "StockoutRiskLevel": score_to_level(stockout_risk_score),
                    "OverstockRiskLevel": score_to_level(overstock_risk_score),
                    "DemandSpikeRiskLevel": score_to_level(demand_spike_risk_score),
                    "SupplierDelayRiskLevel": score_to_level(supplier_delay_risk_score),
                    "InventoryAgeRiskLevel": score_to_level(inventory_age_risk_score),
                    "InventoryRiskScore": inventory_risk_score,
                    "InventoryRiskLevel": score_to_level(inventory_risk_score),
                    "InventoryHealthScore": inventory_health_score,
                    "StockoutCost": stockout_cost,
                    "TotalInventoryCost": total_inventory_cost,
                    "OptimizedInventoryCost": optimized_inventory_cost,
                    "InventorySavings": inventory_savings,
                    "PotentialRevenueLoss": potential_revenue_loss,
                    "ExpectedProfitImprovement": expected_profit_improvement,
                    "UnmetDemandUnits": unmet_demand,
                    "InboundReceiptUnits": inbound_receipts,
                    "PendingInboundUnits": pending_inbound_units,
                    "ReorderToday": reorder_today,
                }
            )
            opening_stock = estimated_stock

    inventory_dataset = pd.DataFrame(rows).sort_values(["SeriesKey", "HorizonDays", "Date"]).reset_index(drop=True)
    inventory_dataset["HighRiskFlag"] = inventory_dataset["InventoryRiskLevel"].isin(["High", "Critical"]).astype(int)
    return inventory_dataset


def summarize_inventory_metrics(dataset: pd.DataFrame) -> pd.DataFrame:
    metrics = (
        dataset.groupby(["SeriesKey", "Product", "Country", "ProductCategory", "HorizonDays"], as_index=False)
        .agg(
            Warehouse=("Warehouse", "first"),
            SupplierLane=("SupplierLane", "first"),
            CurrentStock=("CurrentStock", "first"),
            EstimatedStock=("EstimatedStock", "last"),
            ForecastDemand=("ForecastDemand", "sum"),
            ForecastRevenue=("ForecastRevenue", "sum"),
            DailyDemand=("DailyDemand", "first"),
            WeeklyDemand=("WeeklyDemand", "first"),
            MonthlyDemand=("MonthlyDemand", "first"),
            AnnualDemand=("AnnualDemand", "first"),
            LeadTime=("LeadTime", "first"),
            SupplierLeadTime=("SupplierLeadTime", "first"),
            HoldingCost=("HoldingCost", "sum"),
            OrderingCost=("OrderingCost", "sum"),
            InventoryCarryingCost=("InventoryCarryingCost", "sum"),
            StockValue=("StockValue", "mean"),
            SafetyStock=("SafetyStock", "mean"),
            ReorderPoint=("ReorderPoint", "mean"),
            ReorderQuantity=("ReorderQuantity", "sum"),
            EconomicOrderQuantity=("EconomicOrderQuantity", "first"),
            InventoryTurnover=("InventoryTurnover", "first"),
            DaysOfInventory=("DaysOfInventory", "mean"),
            ServiceLevel=("ServiceLevel", "first"),
            StockCoverageDays=("StockCoverageDays", "min"),
            DemandVariability=("DemandVariability", "first"),
            LeadTimeVariability=("LeadTimeVariability", "first"),
            WarehouseAllocationScore=("WarehouseAllocationScore", "mean"),
            InventoryRiskScore=("InventoryRiskScore", "max"),
            InventoryHealthScore=("InventoryHealthScore", "mean"),
            StockoutCost=("StockoutCost", "sum"),
            TotalInventoryCost=("TotalInventoryCost", "sum"),
            OptimizedInventoryCost=("OptimizedInventoryCost", "sum"),
            InventorySavings=("InventorySavings", "sum"),
            PotentialRevenueLoss=("PotentialRevenueLoss", "sum"),
            ExpectedProfitImprovement=("ExpectedProfitImprovement", "sum"),
            FastMovingItem=("FastMovingItem", "max"),
            SlowMovingItem=("SlowMovingItem", "max"),
            DeadStockCandidate=("DeadStockCandidate", "max"),
            SeasonalProduct=("SeasonalProduct", "max"),
            CriticalProduct=("CriticalProduct", "max"),
            HighValueItem=("HighValueItem", "max"),
            LowValueItem=("LowValueItem", "max"),
            ABCClass=("ABCClass", "first"),
            XYZClass=("XYZClass", "first"),
            ABCXYZMatrix=("ABCXYZMatrix", "first"),
        )
        .sort_values(["HorizonDays", "TotalInventoryCost"], ascending=[True, False])
        .reset_index(drop=True)
    )
    return metrics


def summarize_inventory_risk(dataset: pd.DataFrame) -> pd.DataFrame:
    risk_summary = (
        dataset.groupby(["SeriesKey", "Product", "Country", "ProductCategory", "HorizonDays"], as_index=False)
        .agg(
            InventoryRiskScore=("InventoryRiskScore", "max"),
            InventoryHealthScore=("InventoryHealthScore", "mean"),
            StockoutRiskScore=("StockoutRiskScore", "max"),
            OverstockRiskScore=("OverstockRiskScore", "max"),
            DemandSpikeRiskScore=("DemandSpikeRiskScore", "max"),
            SupplierDelayRiskScore=("SupplierDelayRiskScore", "max"),
            InventoryAgeRiskScore=("InventoryAgeRiskScore", "max"),
            HighRiskDays=("HighRiskFlag", "sum"),
            MinCoverageDays=("StockCoverageDays", "min"),
            MaxUnmetDemandUnits=("UnmetDemandUnits", "max"),
            PotentialRevenueLoss=("PotentialRevenueLoss", "sum"),
        )
        .sort_values(["InventoryRiskScore", "PotentialRevenueLoss"], ascending=False)
        .reset_index(drop=True)
    )
    risk_summary["InventoryRiskLevel"] = risk_summary["InventoryRiskScore"].apply(score_to_level)
    return risk_summary


def create_inventory_dashboard(dataset: pd.DataFrame, metrics: pd.DataFrame, risk_summary: pd.DataFrame, recommendations: pd.DataFrame) -> pd.DataFrame:
    horizon_view = (
        dataset.groupby("HorizonDays", as_index=False)
        .agg(
            ForecastDemand=("ForecastDemand", "sum"),
            ForecastRevenue=("ForecastRevenue", "sum"),
            TotalInventoryCost=("TotalInventoryCost", "sum"),
            InventorySavings=("InventorySavings", "sum"),
            InventoryRiskScore=("InventoryRiskScore", "mean"),
            InventoryHealthScore=("InventoryHealthScore", "mean"),
        )
        .assign(DashboardView="HorizonKPI", EntityType="Horizon", Entity=lambda frame: frame["HorizonDays"].astype(str))
    )
    country_view = (
        metrics.groupby(["Country", "HorizonDays"], as_index=False)
        .agg(
            ForecastDemand=("ForecastDemand", "sum"),
            ForecastRevenue=("ForecastRevenue", "sum"),
            TotalInventoryCost=("TotalInventoryCost", "sum"),
            InventorySavings=("InventorySavings", "sum"),
            InventoryRiskScore=("InventoryRiskScore", "mean"),
            InventoryHealthScore=("InventoryHealthScore", "mean"),
        )
        .assign(DashboardView="CountryInventory", EntityType="Country", Entity=lambda frame: frame["Country"])
    )
    category_view = (
        metrics.groupby(["ProductCategory", "HorizonDays"], as_index=False)
        .agg(
            ForecastDemand=("ForecastDemand", "sum"),
            ForecastRevenue=("ForecastRevenue", "sum"),
            TotalInventoryCost=("TotalInventoryCost", "sum"),
            InventorySavings=("InventorySavings", "sum"),
            InventoryRiskScore=("InventoryRiskScore", "mean"),
            InventoryHealthScore=("InventoryHealthScore", "mean"),
        )
        .assign(DashboardView="CategoryInventory", EntityType="Category", Entity=lambda frame: frame["ProductCategory"])
    )
    warehouse_view = (
        dataset.groupby(["Warehouse", "HorizonDays"], as_index=False)
        .agg(
            EstimatedStock=("EstimatedStock", "sum"),
            StockValue=("StockValue", "sum"),
            WarehouseAllocationScore=("WarehouseAllocationScore", "mean"),
            InventoryRiskScore=("InventoryRiskScore", "mean"),
        )
        .assign(DashboardView="WarehouseUtilization", EntityType="Warehouse", Entity=lambda frame: frame["Warehouse"])
    )
    recommendation_view = (
        recommendations.groupby(["Recommendation", "Priority"], as_index=False)
        .agg(RecommendationCount=("SeriesKey", "count"))
        .assign(DashboardView="RecommendationMix", EntityType="Recommendation", Entity=lambda frame: frame["Recommendation"])
    )
    risk_view = (
        risk_summary.groupby(["InventoryRiskLevel", "HorizonDays"], as_index=False)
        .agg(
            SeriesCount=("SeriesKey", "nunique"),
            PotentialRevenueLoss=("PotentialRevenueLoss", "sum"),
        )
        .assign(DashboardView="RiskDistribution", EntityType="RiskLevel", Entity=lambda frame: frame["InventoryRiskLevel"])
    )

    dashboard = pd.concat(
        [horizon_view, country_view, category_view, warehouse_view, recommendation_view, risk_view],
        ignore_index=True,
        sort=False,
    )
    return dashboard


def create_inventory_recommendations(metrics: pd.DataFrame) -> pd.DataFrame:
    recommendation_rows: list[dict[str, Any]] = []

    def add_recommendation(row: pd.Series, recommendation: str, priority: str, explanation: str, trigger_metric: str, trigger_value: float, suggested_quantity: float = 0.0) -> None:
        recommendation_rows.append(
            {
                "SeriesKey": row["SeriesKey"],
                "Product": row["Product"],
                "Country": row["Country"],
                "ProductCategory": row["ProductCategory"],
                "HorizonDays": int(row["HorizonDays"]),
                "Recommendation": recommendation,
                "Priority": priority,
                "BusinessExplanation": explanation,
                "TriggerMetric": trigger_metric,
                "TriggerValue": float(trigger_value),
                "SuggestedQuantity": float(suggested_quantity),
            }
        )

    peer_coverage = metrics.groupby("ProductCategory")["StockCoverageDays"].mean().to_dict()
    peer_risk = metrics.groupby("Country")["InventoryRiskScore"].mean().to_dict()

    for _, row in metrics.iterrows():
        risk = float(row["InventoryRiskScore"])
        coverage = float(row["StockCoverageDays"])
        reorder_quantity = float(row["ReorderQuantity"])
        revenue_loss = float(row["PotentialRevenueLoss"])
        savings = float(row["InventorySavings"])

        if risk >= 80 and coverage <= float(row["SupplierLeadTime"]):
            add_recommendation(
                row,
                "Emergency Procurement",
                "Critical",
                f"Coverage is down to {coverage:.1f} days against a supplier lead time of {row['SupplierLeadTime']:.1f} days, creating immediate stockout exposure.",
                "InventoryRiskScore",
                risk,
                reorder_quantity,
            )
        elif risk >= 60 and reorder_quantity > 0:
            add_recommendation(
                row,
                "Reorder Today",
                "High",
                f"Projected stock falls below the reorder point while the recommended replenishment quantity is {reorder_quantity:.0f} units.",
                "ReorderQuantity",
                reorder_quantity,
                reorder_quantity,
            )

        if float(row["PotentialRevenueLoss"]) > 0 and risk >= 55:
            add_recommendation(
                row,
                "Increase Stock",
                "High",
                f"Potential revenue loss is estimated at {revenue_loss:.2f}, indicating that incremental stock can protect sales and service levels.",
                "PotentialRevenueLoss",
                revenue_loss,
                max(reorder_quantity, float(row["EconomicOrderQuantity"])),
            )

        if coverage > 90 and bool(row["SlowMovingItem"]):
            add_recommendation(
                row,
                "Reduce Stock",
                "Medium",
                f"Coverage has stretched to {coverage:.1f} days on a slow-moving item, tying up working capital without proportional demand support.",
                "StockCoverageDays",
                coverage,
            )
            add_recommendation(
                row,
                "Delay Purchase",
                "Medium",
                "Existing stock coverage materially exceeds the near-term demand window, so postponing the next purchase will reduce carrying cost.",
                "StockCoverageDays",
                coverage,
            )

        if bool(row["DeadStockCandidate"]) and coverage > 120:
            add_recommendation(
                row,
                "Clear Dead Stock",
                "High",
                "This SKU is flagged as a dead-stock candidate with prolonged inventory coverage, so liquidation should be prioritized.",
                "StockCoverageDays",
                coverage,
            )
            add_recommendation(
                row,
                "Discount Recommendation",
                "High",
                "Promotional pricing is recommended to accelerate sell-through and release trapped working capital.",
                "InventorySavings",
                savings,
            )

        category_coverage = float(peer_coverage.get(row["ProductCategory"], coverage))
        if risk >= 60 and category_coverage > coverage + 20:
            add_recommendation(
                row,
                "Warehouse Transfer",
                "Medium",
                "Peer inventory coverage in the same category is materially higher elsewhere, suggesting that internal transfer can reduce urgent buy pressure.",
                "PeerCategoryCoverage",
                category_coverage,
            )

        if float(row["SupplierLeadTime"]) >= 12 or float(row["LeadTimeVariability"]) >= 3.5:
            add_recommendation(
                row,
                "Supplier Review",
                "Medium",
                "Supplier lead time and variability are high enough to justify a sourcing review and tighter inbound performance management.",
                "SupplierLeadTime",
                float(row["SupplierLeadTime"]),
            )

        if bool(row["FastMovingItem"]) and bool(row["XYZClass"] == "X") and reorder_quantity > float(row["EconomicOrderQuantity"]) * 0.80:
            add_recommendation(
                row,
                "Bulk Purchase Opportunity",
                "Medium",
                "Stable demand and repeated replenishment pressure indicate an opportunity to buy closer to economic order quantity and reduce ordering friction.",
                "ReorderQuantity",
                reorder_quantity,
                max(reorder_quantity, float(row["EconomicOrderQuantity"])),
            )

        if risk >= 55 and float(peer_risk.get(row["Country"], risk)) >= 55:
            add_recommendation(
                row,
                "Demand Buffer Optimization",
                "Medium",
                "Country-level inventory risk is elevated, so increasing demand buffer assumptions can improve resilience for this replenishment lane.",
                "CountryRiskScore",
                float(peer_risk.get(row["Country"], risk)),
                max(reorder_quantity, float(row["SafetyStock"])),
            )

    recommendations = pd.DataFrame(recommendation_rows)
    if recommendations.empty:
        return pd.DataFrame(
            columns=[
                "SeriesKey",
                "Product",
                "Country",
                "ProductCategory",
                "HorizonDays",
                "Recommendation",
                "Priority",
                "BusinessExplanation",
                "TriggerMetric",
                "TriggerValue",
                "SuggestedQuantity",
            ]
        )
    return recommendations.drop_duplicates().sort_values(["Priority", "HorizonDays", "Product"]).reset_index(drop=True)


def inventory_feature_columns() -> list[str]:
    return [
        "CurrentStock",
        "EstimatedStock",
        "ForecastDemand",
        "DailyDemand",
        "WeeklyDemand",
        "MonthlyDemand",
        "AnnualDemand",
        "LeadTime",
        "SupplierLeadTime",
        "HoldingCost",
        "OrderingCost",
        "InventoryCarryingCost",
        "StockValue",
        "SafetyStock",
        "ReorderPoint",
        "ReorderQuantity",
        "EconomicOrderQuantity",
        "InventoryTurnover",
        "DaysOfInventory",
        "ServiceLevel",
        "StockCoverageDays",
        "DemandVariability",
        "LeadTimeVariability",
        "DemandBufferUnits",
        "WarehouseAllocationScore",
        "StockoutCost",
        "TotalInventoryCost",
        "OptimizedInventoryCost",
        "InventorySavings",
        "PotentialRevenueLoss",
        "ExpectedProfitImprovement",
        "UnmetDemandUnits",
        "InboundReceiptUnits",
        "PendingInboundUnits",
        "HorizonDays",
        "FastMovingItem",
        "SlowMovingItem",
        "DeadStockCandidate",
        "SeasonalProduct",
        "CriticalProduct",
        "HighValueItem",
        "LowValueItem",
    ]


def model_classes(model: Any) -> np.ndarray | None:
    classes = getattr(model, "classes_", None)
    if classes is not None:
        return np.asarray(classes)
    if isinstance(model, Pipeline):
        classifier = model.named_steps.get("classifier")
        if classifier is not None:
            classifier_classes = getattr(classifier, "classes_", None)
            if classifier_classes is not None:
                return np.asarray(classifier_classes)
    return None


def positive_class_score(model: Pipeline, features: pd.DataFrame) -> np.ndarray:
    if hasattr(model, "predict_proba"):
        probabilities = np.asarray(model.predict_proba(features), dtype=float)
        if probabilities.ndim == 1:
            return probabilities
        classes = model_classes(model)
        if classes is not None and classes.size:
            positive_match = np.where(classes == 1)[0]
            if positive_match.size:
                return probabilities[:, int(positive_match[0])]
            if classes.size == 1:
                return np.full(len(features), float(classes[0] == 1), dtype=float)
        if probabilities.shape[1] == 1:
            return probabilities[:, 0]
        return probabilities[:, -1]
    if hasattr(model, "decision_function"):
        raw = np.asarray(model.decision_function(features), dtype=float)
        return 1.0 / (1.0 + np.exp(-raw))
    return np.asarray(model.predict(features), dtype=float)


def build_prediction_frame(
    dataset: pd.DataFrame,
    predicted_probabilities: np.ndarray,
    predicted_labels: np.ndarray,
) -> pd.DataFrame:
    prediction_frame = dataset[["SeriesKey", "Date", "HorizonDays"]].copy()
    prediction_frame["PredictedHighRiskProbability"] = np.asarray(predicted_probabilities, dtype=float)
    prediction_frame["PredictedHighRiskFlag"] = np.asarray(predicted_labels, dtype=int)
    return prediction_frame


def train_inventory_risk_models(dataset: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any], pd.DataFrame]:
    feature_columns = inventory_feature_columns()
    features = dataset[feature_columns].copy()
    for column in features.columns:
        features[column] = pd.to_numeric(features[column], errors="coerce")
    features = features.fillna(0.0)
    target = dataset["HighRiskFlag"].astype(int)
    catalog = inventory_model_catalog()
    min_class_count = int(target.value_counts().min()) if not target.empty else 0

    if target.nunique() < 2 or min_class_count < 2:
        rows = []
        for spec in catalog.values():
            rows.append(
                {
                    "model_name": spec.name,
                    "status": "unavailable",
                    "reason": "Inventory risk target does not contain enough class diversity for stratified evaluation.",
                    "accuracy": np.nan,
                    "precision": np.nan,
                    "recall": np.nan,
                    "f1": np.nan,
                    "roc_auc": np.nan,
                    "confusion_matrix": "[]",
                }
            )
        constant_class = int(target.iloc[0]) if not target.empty else 0
        fallback_model = classification_pipeline(DummyClassifier(strategy="constant", constant=constant_class))
        fallback_model.fit(features, target)
        predicted_labels = np.asarray(fallback_model.predict(features), dtype=int)
        predicted_probabilities = positive_class_score(fallback_model, features)
        fallback_metrics = {
            "model_name": "Single Class Baseline",
            "status": "fallback",
            "reason": f"All observations map to inventory risk class {constant_class}; using a constant baseline to keep artifact generation operational.",
            "accuracy": float(accuracy_score(target, predicted_labels)),
            "precision": float(precision_score(target, predicted_labels, zero_division=0)),
            "recall": float(recall_score(target, predicted_labels, zero_division=0)),
            "f1": float(f1_score(target, predicted_labels, zero_division=0)),
            "roc_auc": np.nan,
            "confusion_matrix": json.dumps(confusion_matrix(target, predicted_labels, labels=[0, 1]).tolist()),
        }
        rows.append(fallback_metrics)
        best_payload = {
            "model_name": "Single Class Baseline",
            "metrics": fallback_metrics,
            "estimator": fallback_model,
            "feature_columns": feature_columns,
        }
        prediction_frame = build_prediction_frame(dataset, predicted_probabilities, predicted_labels)
        model_metrics = (
            pd.DataFrame(rows)
            .sort_values(["status", "f1", "roc_auc", "accuracy"], ascending=[True, False, False, False])
            .reset_index(drop=True)
        )
        return model_metrics, best_payload, prediction_frame

    X_train, X_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=0.25,
        random_state=DEFAULT_RANDOM_STATE,
        stratify=target,
    )

    rows: list[dict[str, Any]] = []
    best_payload: dict[str, Any] = {}
    best_score = (-1.0, -1.0, -1.0)

    for spec in catalog.values():
        if not spec.available or spec.factory is None:
            rows.append(
                {
                    "model_name": spec.name,
                    "status": "unavailable",
                    "reason": spec.reason_unavailable or "Optional dependency is unavailable.",
                    "accuracy": np.nan,
                    "precision": np.nan,
                    "recall": np.nan,
                    "f1": np.nan,
                    "roc_auc": np.nan,
                    "confusion_matrix": "[]",
                }
            )
            continue

        try:
            model = spec.factory()
            model.fit(X_train, y_train)
            predicted_labels = model.predict(X_test)
            predicted_scores = positive_class_score(model, X_test)
            metrics_row = {
                "model_name": spec.name,
                "status": "evaluated",
                "reason": "",
                "accuracy": float(accuracy_score(y_test, predicted_labels)),
                "precision": float(precision_score(y_test, predicted_labels, zero_division=0)),
                "recall": float(recall_score(y_test, predicted_labels, zero_division=0)),
                "f1": float(f1_score(y_test, predicted_labels, zero_division=0)),
                "roc_auc": float(roc_auc_score(y_test, predicted_scores)),
                "confusion_matrix": json.dumps(confusion_matrix(y_test, predicted_labels, labels=[0, 1]).tolist()),
            }
            rows.append(metrics_row)

            ranking_key = (metrics_row["f1"], metrics_row["roc_auc"], metrics_row["accuracy"])
            if ranking_key > best_score:
                best_score = ranking_key
                best_payload = {
                    "model_name": spec.name,
                    "metrics": metrics_row,
                    "estimator": model,
                }
        except Exception as exc:
            rows.append(
                {
                    "model_name": spec.name,
                    "status": "failed",
                    "reason": str(exc),
                    "accuracy": np.nan,
                    "precision": np.nan,
                    "recall": np.nan,
                    "f1": np.nan,
                    "roc_auc": np.nan,
                    "confusion_matrix": "[]",
                }
            )

    model_metrics = pd.DataFrame(rows).sort_values(["status", "f1", "roc_auc", "accuracy"], ascending=[True, False, False, False]).reset_index(drop=True)
    if not best_payload:
        return model_metrics, {}, pd.DataFrame()

    final_model = catalog[best_payload["model_name"]].factory()
    final_model.fit(features, target)
    predicted_probabilities = positive_class_score(final_model, features)
    predicted_labels = (predicted_probabilities >= 0.5).astype(int)
    prediction_frame = build_prediction_frame(dataset, predicted_probabilities, predicted_labels)
    best_payload["estimator"] = final_model
    best_payload["feature_columns"] = feature_columns
    return model_metrics, best_payload, prediction_frame


def enrich_with_model_predictions(dataset: pd.DataFrame, prediction_frame: pd.DataFrame) -> pd.DataFrame:
    if prediction_frame.empty:
        dataset["PredictedHighRiskProbability"] = np.nan
        dataset["PredictedHighRiskFlag"] = np.nan
        return dataset
    enriched = dataset.merge(prediction_frame, on=["SeriesKey", "Date", "HorizonDays"], how="left")
    return enriched


def create_inventory_visualizations(
    dataset: pd.DataFrame,
    metrics: pd.DataFrame,
    risk_summary: pd.DataFrame,
    dashboard: pd.DataFrame,
    recommendations: pd.DataFrame,
    abc_analysis: pd.DataFrame,
    xyz_analysis: pd.DataFrame,
    abc_xyz_matrix: pd.DataFrame,
    model_metrics: pd.DataFrame,
    figures_dir: Path,
) -> list[Path]:
    figures_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")
    paths: list[Path] = []
    counter = 1

    def save(fig: plt.Figure, name: str) -> Path:
        nonlocal counter
        path = figures_dir / f"inventory_{counter:02d}_{slugify(name)}.png"
        backup_existing_file(path)
        fig.tight_layout()
        fig.savefig(path, dpi=250, bbox_inches="tight")
        plt.close(fig)
        paths.append(path)
        counter += 1
        return path

    if not abc_analysis.empty:
        abc_sorted = abc_analysis.sort_values("TotalRevenue", ascending=False)
        fig, ax = plt.subplots(figsize=(12, 4))
        sns.barplot(data=abc_sorted, x="Product", y="TotalRevenue", hue="ABCClass", ax=ax)
        ax.set_title("ABC Analysis")
        ax.tick_params(axis="x", rotation=45)
        save(fig, "abc_analysis")

        fig, ax = plt.subplots(figsize=(12, 4))
        ax.plot(range(1, len(abc_sorted) + 1), abc_sorted["CumulativeRevenueShare"] * 100.0, marker="o")
        ax.axhline(80, linestyle="--", color="#ff7f0e")
        ax.axhline(95, linestyle="--", color="#2ca02c")
        ax.set_title("Pareto Analysis")
        ax.set_ylabel("Cumulative Revenue Share %")
        save(fig, "pareto_analysis")

    if not xyz_analysis.empty:
        fig, ax = plt.subplots(figsize=(12, 4))
        sns.barplot(data=xyz_analysis.sort_values("DemandCV", ascending=False), x="Product", y="DemandCV", hue="XYZClass", ax=ax)
        ax.set_title("XYZ Analysis")
        ax.tick_params(axis="x", rotation=45)
        save(fig, "xyz_analysis")

        fig, ax = plt.subplots(figsize=(8, 4))
        xyz_analysis["XYZClass"].value_counts().sort_index().plot(kind="bar", ax=ax)
        ax.set_title("XYZ Class Distribution")
        save(fig, "xyz_class_distribution")

    if not abc_xyz_matrix.empty:
        matrix_count = abc_xyz_matrix.pivot(index="ABCClass", columns="XYZClass", values="ItemCount").fillna(0)
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.heatmap(matrix_count, annot=True, fmt=".0f", cmap="Blues", ax=ax)
        ax.set_title("ABC-XYZ Matrix")
        save(fig, "abc_xyz_matrix")

        matrix_value = abc_xyz_matrix.pivot(index="ABCClass", columns="XYZClass", values="StockValue").fillna(0)
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.heatmap(matrix_value, annot=True, fmt=".0f", cmap="YlOrRd", ax=ax)
        ax.set_title("ABC-XYZ Stock Value")
        save(fig, "abc_xyz_stock_value")

    if not metrics.empty:
        fig, ax = plt.subplots(figsize=(10, 4))
        sns.scatterplot(data=metrics, x="AnnualDemand", y="EconomicOrderQuantity", size="StockValue", hue="ProductCategory", ax=ax)
        ax.set_title("EOQ Curve")
        save(fig, "eoq_curve")

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.histplot(metrics["SafetyStock"], bins=20, kde=True, ax=ax)
        ax.set_title("Safety Stock Distribution")
        save(fig, "safety_stock_distribution")

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.histplot(metrics["ReorderPoint"], bins=20, kde=True, ax=ax)
        ax.set_title("Reorder Point Analysis")
        save(fig, "reorder_point_analysis")

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.histplot(metrics["InventoryTurnover"], bins=20, kde=True, ax=ax)
        ax.set_title("Inventory Turnover")
        save(fig, "inventory_turnover")

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.histplot(metrics["DaysOfInventory"], bins=20, kde=True, ax=ax)
        ax.set_title("Inventory Aging")
        save(fig, "inventory_aging")

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.histplot(metrics["ServiceLevel"], bins=20, kde=True, ax=ax)
        ax.set_title("Service Level Distribution")
        save(fig, "service_level_distribution")

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.histplot(metrics["StockCoverageDays"], bins=20, kde=True, ax=ax)
        ax.set_title("Stock Coverage Days")
        save(fig, "stock_coverage_days")

        fig, ax = plt.subplots(figsize=(10, 5))
        sns.scatterplot(data=metrics, x="DemandVariability", y="LeadTime", size="StockValue", hue="InventoryRiskScore", palette="coolwarm", ax=ax)
        ax.set_title("Demand Variability vs Lead Time")
        save(fig, "demand_variability_vs_lead_time")

        fig, ax = plt.subplots(figsize=(10, 5))
        sns.scatterplot(data=metrics, x="SafetyStock", y="ReorderPoint", size="EconomicOrderQuantity", hue="ProductCategory", ax=ax)
        ax.set_title("Safety Stock vs Reorder Point")
        save(fig, "safety_stock_vs_reorder_point")

        fig, ax = plt.subplots(figsize=(10, 5))
        sns.scatterplot(data=metrics, x="StockValue", y="InventoryCarryingCost", size="ForecastRevenue", hue="InventoryRiskScore", palette="viridis", ax=ax)
        ax.set_title("Stock Value vs Carrying Cost")
        save(fig, "stock_value_vs_carrying_cost")

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.barplot(data=metrics.groupby("Country", as_index=False)["StockValue"].sum().sort_values("StockValue", ascending=False), x="Country", y="StockValue", ax=ax)
        ax.set_title("Country Inventory")
        ax.tick_params(axis="x", rotation=45)
        save(fig, "country_inventory")

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.barplot(data=metrics.groupby("ProductCategory", as_index=False)["StockValue"].sum().sort_values("StockValue", ascending=False), x="ProductCategory", y="StockValue", ax=ax)
        ax.set_title("Category Inventory")
        save(fig, "category_inventory")

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.histplot(metrics["WarehouseAllocationScore"], bins=20, kde=True, ax=ax)
        ax.set_title("Warehouse Allocation Score")
        save(fig, "warehouse_allocation_score")

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.barplot(data=metrics.groupby("ProductCategory", as_index=False)["WarehouseAllocationScore"].mean().sort_values("WarehouseAllocationScore", ascending=False), x="ProductCategory", y="WarehouseAllocationScore", ax=ax)
        ax.set_title("Warehouse Allocation By Category")
        save(fig, "warehouse_allocation_by_category")

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.barplot(data=metrics.groupby("Product", as_index=False)["InventorySavings"].sum().sort_values("InventorySavings", ascending=False).head(10), x="Product", y="InventorySavings", ax=ax)
        ax.set_title("Inventory Savings")
        ax.tick_params(axis="x", rotation=45)
        save(fig, "inventory_savings")

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.barplot(data=metrics.groupby("Product", as_index=False)["PotentialRevenueLoss"].sum().sort_values("PotentialRevenueLoss", ascending=False).head(10), x="Product", y="PotentialRevenueLoss", ax=ax)
        ax.set_title("Potential Revenue Loss")
        ax.tick_params(axis="x", rotation=45)
        save(fig, "potential_revenue_loss")

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.barplot(data=metrics.groupby("Product", as_index=False)["ExpectedProfitImprovement"].sum().sort_values("ExpectedProfitImprovement", ascending=False).head(10), x="Product", y="ExpectedProfitImprovement", ax=ax)
        ax.set_title("Expected Profit Improvement")
        ax.tick_params(axis="x", rotation=45)
        save(fig, "expected_profit_improvement")

        classification_views = [
            ("Fast Moving Items", "FastMovingItem"),
            ("Slow Moving Items", "SlowMovingItem"),
            ("Dead Stock", "DeadStockCandidate"),
            ("Critical Products", "CriticalProduct"),
            ("High Value Items", "HighValueItem"),
            ("Low Value Items", "LowValueItem"),
        ]
        for title, column in classification_views:
            subset = metrics[metrics[column]].sort_values("ForecastRevenue", ascending=False).head(10)
            if subset.empty:
                continue
            fig, ax = plt.subplots(figsize=(10, 4))
            sns.barplot(data=subset, x="Product", y="ForecastRevenue", ax=ax)
            ax.set_title(title)
            ax.tick_params(axis="x", rotation=45)
            save(fig, title)

        country_stock_values = metrics.groupby("Country", as_index=False)["StockValue"].sum().sort_values("StockValue", ascending=False).head(10)
        fig, ax = plt.subplots(figsize=(8, 4))
        draw_simple_treemap(ax, country_stock_values["StockValue"], country_stock_values["Country"], "Country Inventory Treemap")
        save(fig, "country_inventory_treemap")

        category_stock_values = metrics.groupby("ProductCategory", as_index=False)["StockValue"].sum().sort_values("StockValue", ascending=False).head(10)
        fig, ax = plt.subplots(figsize=(8, 4))
        draw_simple_treemap(ax, category_stock_values["StockValue"], category_stock_values["ProductCategory"], "Category Inventory Treemap")
        save(fig, "category_inventory_treemap")

        cost_components = metrics[["HoldingCost", "OrderingCost", "StockoutCost", "InventorySavings"]].sum()
        fig, ax = plt.subplots(figsize=(9, 4))
        draw_waterfall(
            ax,
            ["Holding", "Ordering", "Stockout", "Savings"],
            [
                float(cost_components.get("HoldingCost", 0.0)),
                float(cost_components.get("OrderingCost", 0.0)),
                float(cost_components.get("StockoutCost", 0.0)),
                -float(cost_components.get("InventorySavings", 0.0)),
            ],
            "Inventory Cost Breakdown",
        )
        save(fig, "inventory_cost_breakdown")

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.barplot(data=metrics.groupby("Warehouse", as_index=False)["StockValue"].sum().sort_values("StockValue", ascending=False), x="Warehouse", y="StockValue", ax=ax)
        ax.set_title("Warehouse Utilization")
        save(fig, "warehouse_utilization")

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.barplot(data=metrics.groupby("Country", as_index=False)["SupplierLeadTime"].mean().sort_values("SupplierLeadTime", ascending=False), x="Country", y="SupplierLeadTime", ax=ax)
        ax.set_title("Supplier Lead Time")
        ax.tick_params(axis="x", rotation=45)
        save(fig, "supplier_lead_time")

    if not dataset.empty:
        stockout_heatmap = dataset.groupby(["Product", "HorizonDays"], as_index=False)["StockoutRiskScore"].max().pivot(index="Product", columns="HorizonDays", values="StockoutRiskScore").fillna(0)
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.heatmap(stockout_heatmap, cmap="Reds", annot=True, fmt=".0f", ax=ax)
        ax.set_title("Stockout Heatmap")
        save(fig, "stockout_heatmap")

        overstock_heatmap = dataset.groupby(["Product", "HorizonDays"], as_index=False)["OverstockRiskScore"].max().pivot(index="Product", columns="HorizonDays", values="OverstockRiskScore").fillna(0)
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.heatmap(overstock_heatmap, cmap="Blues", annot=True, fmt=".0f", ax=ax)
        ax.set_title("Overstock Heatmap")
        save(fig, "overstock_heatmap")

        fig, ax = plt.subplots(figsize=(10, 5))
        sns.scatterplot(data=dataset, x="ForecastDemand", y="EstimatedStock", hue="InventoryRiskLevel", size="HorizonDays", ax=ax)
        ax.set_title("Forecast vs Inventory")
        save(fig, "forecast_vs_inventory")

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.histplot(dataset["InventoryHealthScore"], bins=25, kde=True, ax=ax)
        ax.set_title("Inventory Health Score")
        save(fig, "inventory_health_score")

        fig, ax = plt.subplots(figsize=(10, 4))
        dataset["InventoryRiskLevel"].value_counts().reindex(["Low", "Medium", "High", "Critical"]).plot(kind="bar", ax=ax)
        ax.set_title("Risk Dashboard")
        save(fig, "risk_dashboard")

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.barplot(data=dataset.groupby("HorizonDays", as_index=False)["ForecastDemand"].sum(), x="HorizonDays", y="ForecastDemand", ax=ax)
        ax.set_title("Forecast Horizon Demand")
        save(fig, "forecast_horizon_demand")

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.histplot(dataset["ReorderQuantity"], bins=25, kde=True, ax=ax)
        ax.set_title("Reorder Quantity Distribution")
        save(fig, "reorder_quantity_distribution")

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.histplot(dataset["LeadTimeVariability"], bins=25, kde=True, ax=ax)
        ax.set_title("Lead Time Variability")
        save(fig, "lead_time_variability")

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.histplot(dataset["OrderingCost"], bins=25, kde=True, ax=ax)
        ax.set_title("Ordering Cost Distribution")
        save(fig, "ordering_cost_distribution")

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.histplot(dataset["HoldingCost"], bins=25, kde=True, ax=ax)
        ax.set_title("Holding Cost Distribution")
        save(fig, "holding_cost_distribution")

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.barplot(data=dataset.groupby("HorizonDays", as_index=False)["TotalInventoryCost"].sum(), x="HorizonDays", y="TotalInventoryCost", ax=ax)
        ax.set_title("Total Inventory Cost")
        save(fig, "total_inventory_cost")

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.barplot(data=dataset.groupby("ProductCategory", as_index=False)["InventoryHealthScore"].mean().sort_values("InventoryHealthScore", ascending=False), x="ProductCategory", y="InventoryHealthScore", ax=ax)
        ax.set_title("Inventory Health By Category")
        save(fig, "inventory_health_by_category")

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.barplot(data=dataset.groupby("Country", as_index=False)["InventoryHealthScore"].mean().sort_values("InventoryHealthScore", ascending=False), x="Country", y="InventoryHealthScore", ax=ax)
        ax.set_title("Inventory Health By Country")
        ax.tick_params(axis="x", rotation=45)
        save(fig, "inventory_health_by_country")

        fig, ax = plt.subplots(figsize=(10, 5))
        sns.scatterplot(data=dataset, x="InventoryRiskScore", y="InventoryHealthScore", hue="ProductCategory", size="ForecastRevenue", ax=ax)
        ax.set_title("Inventory Health vs Risk")
        save(fig, "inventory_health_vs_risk")

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.barplot(data=dataset.groupby("Country", as_index=False)["SupplierDelayRiskScore"].mean().sort_values("SupplierDelayRiskScore", ascending=False), x="Country", y="SupplierDelayRiskScore", ax=ax)
        ax.set_title("Supplier Delay Risk By Country")
        ax.tick_params(axis="x", rotation=45)
        save(fig, "supplier_delay_risk_by_country")

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.barplot(data=dataset.groupby("ProductCategory", as_index=False)["DemandSpikeRiskScore"].mean().sort_values("DemandSpikeRiskScore", ascending=False), x="ProductCategory", y="DemandSpikeRiskScore", ax=ax)
        ax.set_title("Demand Spike Risk By Category")
        save(fig, "demand_spike_risk_by_category")

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.barplot(data=dataset.groupby("Product", as_index=False)["InventoryAgeRiskScore"].mean().sort_values("InventoryAgeRiskScore", ascending=False).head(10), x="Product", y="InventoryAgeRiskScore", ax=ax)
        ax.set_title("Inventory Age Risk")
        ax.tick_params(axis="x", rotation=45)
        save(fig, "inventory_age_risk")

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.barplot(data=dataset.groupby("HorizonDays", as_index=False)["StockoutRiskScore"].mean(), x="HorizonDays", y="StockoutRiskScore", ax=ax)
        ax.set_title("Stockout Risk By Horizon")
        save(fig, "stockout_risk_by_horizon")

        fig, ax = plt.subplots(figsize=(10, 4))
        sns.barplot(data=dataset.groupby("HorizonDays", as_index=False)["OverstockRiskScore"].mean(), x="HorizonDays", y="OverstockRiskScore", ax=ax)
        ax.set_title("Overstock Risk By Horizon")
        save(fig, "overstock_risk_by_horizon")

        top_products = dataset.groupby("Product", as_index=False)["ForecastRevenue"].sum().sort_values("ForecastRevenue", ascending=False).head(5)["Product"].tolist()
        for product in top_products:
            subset = dataset[dataset["Product"] == product].sort_values("Date")
            fig, ax = plt.subplots(figsize=(12, 4))
            ax.plot(subset["Date"], subset["ForecastDemand"], label="Forecast Demand")
            ax.plot(subset["Date"], subset["EstimatedStock"], label="Estimated Stock")
            ax.set_title(f"Product Dashboard - {product}")
            ax.legend()
            save(fig, f"product_dashboard_{product}")

        for horizon in sorted(dataset["HorizonDays"].dropna().unique().tolist()):
            subset = dataset[dataset["HorizonDays"] == horizon].groupby("Date", as_index=False).agg(ForecastDemand=("ForecastDemand", "sum"), EstimatedStock=("EstimatedStock", "sum"), TotalInventoryCost=("TotalInventoryCost", "sum"))
            fig, ax = plt.subplots(figsize=(12, 4))
            ax.plot(subset["Date"], subset["ForecastDemand"], label="Forecast Demand")
            ax.plot(subset["Date"], subset["EstimatedStock"], label="Estimated Stock")
            ax.set_title(f"Forecast vs Inventory - {horizon} Days")
            ax.legend()
            save(fig, f"forecast_vs_inventory_{horizon}")

            fig, ax = plt.subplots(figsize=(12, 4))
            ax.plot(subset["Date"], subset["TotalInventoryCost"], color="#d62728")
            ax.set_title(f"Cost Dashboard - {horizon} Days")
            save(fig, f"cost_dashboard_{horizon}")

        category_country = dataset.groupby(["Country", "ProductCategory"], as_index=False).agg(EstimatedStock=("EstimatedStock", "sum"))
        if not category_country.empty:
            pivot = category_country.pivot(index="Country", columns="ProductCategory", values="EstimatedStock").fillna(0)
            fig, ax = plt.subplots(figsize=(8, 5))
            sns.heatmap(pivot, cmap="crest", ax=ax)
            ax.set_title("Country Category Inventory")
            save(fig, "country_category_inventory")

    if not dashboard.empty:
        horizon_dashboard = dashboard[dashboard["DashboardView"] == "HorizonKPI"].copy()
        if not horizon_dashboard.empty:
            fig, ax = plt.subplots(figsize=(10, 4))
            sns.barplot(data=horizon_dashboard, x="HorizonDays", y="InventorySavings", ax=ax)
            ax.set_title("Business KPI Dashboard")
            save(fig, "business_kpi_dashboard")

            fig, ax = plt.subplots(figsize=(10, 4))
            sns.barplot(data=horizon_dashboard, x="HorizonDays", y="InventoryRiskScore", ax=ax)
            ax.set_title("Executive Dashboard Preview")
            save(fig, "executive_dashboard_preview")

    if not risk_summary.empty:
        fig, ax = plt.subplots(figsize=(10, 4))
        sns.barplot(data=risk_summary.head(10), x="Product", y="InventoryRiskScore", hue="InventoryRiskLevel", ax=ax)
        ax.set_title("Top Inventory Risk")
        ax.tick_params(axis="x", rotation=45)
        save(fig, "top_inventory_risk")

    if not recommendations.empty:
        recommendation_counts = recommendations["Recommendation"].value_counts().reset_index()
        recommendation_counts.columns = ["Recommendation", "Count"]
        fig, ax = plt.subplots(figsize=(10, 4))
        sns.barplot(data=recommendation_counts, x="Recommendation", y="Count", ax=ax)
        ax.set_title("Inventory Recommendation Mix")
        ax.tick_params(axis="x", rotation=45)
        save(fig, "inventory_recommendation_mix")

        action_map = {
            "Reorder Today": "reorder_today_opportunities",
            "Emergency Procurement": "emergency_procurement_opportunities",
            "Delay Purchase": "delay_purchase_opportunities",
            "Supplier Review": "supplier_review_opportunities",
            "Discount Recommendation": "discount_recommendation_opportunities",
        }
        for recommendation, filename in action_map.items():
            subset = recommendations[recommendations["Recommendation"] == recommendation].head(10)
            if subset.empty:
                continue
            fig, ax = plt.subplots(figsize=(10, 4))
            sns.barplot(data=subset, x="Product", y="TriggerValue", ax=ax)
            ax.set_title(recommendation)
            ax.tick_params(axis="x", rotation=45)
            save(fig, filename)

    evaluated_models = model_metrics[model_metrics["status"] == "evaluated"].copy()
    if not evaluated_models.empty:
        for metric in ["accuracy", "f1", "roc_auc"]:
            fig, ax = plt.subplots(figsize=(8, 4))
            sns.barplot(data=evaluated_models.sort_values(metric, ascending=False), x="model_name", y=metric, ax=ax)
            ax.set_title(f"Inventory ML {metric.upper()}")
            ax.tick_params(axis="x", rotation=45)
            save(fig, f"inventory_ml_{metric}")

        best_row = evaluated_models.sort_values(["f1", "roc_auc", "accuracy"], ascending=False).iloc[0]
        confusion = np.asarray(json.loads(best_row["confusion_matrix"]), dtype=float)
        if confusion.size:
            fig, ax = plt.subplots(figsize=(4, 4))
            sns.heatmap(confusion, annot=True, fmt=".0f", cmap="Blues", ax=ax)
            ax.set_title("Confusion Matrix")
            ax.set_xlabel("Predicted")
            ax.set_ylabel("Actual")
            save(fig, "confusion_matrix")

    if len(paths) < 70 and not dataset.empty:
        for product in dataset["Product"].drop_duplicates().tolist():
            if len(paths) >= 70:
                break
            subset = dataset[dataset["Product"] == product].groupby("Date", as_index=False)["InventoryRiskScore"].mean()
            fig, ax = plt.subplots(figsize=(12, 4))
            ax.plot(subset["Date"], subset["InventoryRiskScore"])
            ax.set_title(f"Risk Trend - {product}")
            save(fig, f"risk_trend_{product}")

    return paths


def save_inventory_artifacts(
    inventory_dataset: pd.DataFrame,
    inventory_metrics: pd.DataFrame,
    inventory_risk: pd.DataFrame,
    inventory_dashboard: pd.DataFrame,
    inventory_recommendations: pd.DataFrame,
    abc_analysis: pd.DataFrame,
    xyz_analysis: pd.DataFrame,
    abc_xyz_matrix: pd.DataFrame,
    best_model_payload: dict[str, Any],
    model_metrics: pd.DataFrame,
    output_dir: Path,
    models_dir: Path,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)
    artifact_paths = {
        "inventory_dataset": output_dir / "inventory_dataset.csv",
        "inventory_metrics": output_dir / "inventory_metrics.csv",
        "inventory_risk": output_dir / "inventory_risk.csv",
        "inventory_dashboard": output_dir / "inventory_dashboard.csv",
        "inventory_recommendations": output_dir / "inventory_recommendations.csv",
        "abc_analysis": output_dir / "abc_analysis.csv",
        "xyz_analysis": output_dir / "xyz_analysis.csv",
        "abc_xyz_matrix": output_dir / "abc_xyz_matrix.csv",
        "inventory_risk_model": models_dir / "inventory_risk_model.pkl",
        "inventory_pipeline": models_dir / "inventory_pipeline.pkl",
        "inventory_scaler": models_dir / "inventory_scaler.pkl",
    }

    write_dataframe(inventory_dataset, artifact_paths["inventory_dataset"])
    write_dataframe(inventory_metrics, artifact_paths["inventory_metrics"])
    write_dataframe(inventory_risk, artifact_paths["inventory_risk"])
    write_dataframe(inventory_dashboard, artifact_paths["inventory_dashboard"])
    write_dataframe(inventory_recommendations, artifact_paths["inventory_recommendations"])
    write_dataframe(abc_analysis, artifact_paths["abc_analysis"])
    write_dataframe(xyz_analysis, artifact_paths["xyz_analysis"])
    write_dataframe(abc_xyz_matrix, artifact_paths["abc_xyz_matrix"])

    model_payload = {
        "best_model_name": best_model_payload.get("model_name", "Unavailable"),
        "metrics": best_model_payload.get("metrics", {}),
        "feature_columns": best_model_payload.get("feature_columns", inventory_feature_columns()),
        "estimator": best_model_payload.get("estimator"),
        "model_metrics": model_metrics.to_dict(orient="records"),
    }
    pipeline_payload = {
        "best_model_name": best_model_payload.get("model_name", "Unavailable"),
        "feature_columns": best_model_payload.get("feature_columns", inventory_feature_columns()),
        "target": "HighRiskFlag",
        "recommendation_priority_order": ["Critical", "High", "Medium", "Low"],
    }
    scaler_payload: Any = {
        "status": "not_required",
        "model_name": best_model_payload.get("model_name", "Unavailable"),
        "reason": "The selected inventory classifier does not expose a standalone persisted scaler artifact.",
    }
    estimator = best_model_payload.get("estimator")
    if isinstance(estimator, Pipeline) and "scaler" in estimator.named_steps:
        scaler_payload = estimator.named_steps["scaler"]

    write_joblib(model_payload, artifact_paths["inventory_risk_model"])
    write_joblib(pipeline_payload, artifact_paths["inventory_pipeline"])
    write_joblib(scaler_payload, artifact_paths["inventory_scaler"])
    return artifact_paths


def write_inventory_reports(
    inventory_dataset: pd.DataFrame,
    inventory_metrics: pd.DataFrame,
    inventory_risk: pd.DataFrame,
    inventory_dashboard: pd.DataFrame,
    inventory_recommendations: pd.DataFrame,
    model_metrics: pd.DataFrame,
    best_model_payload: dict[str, Any],
    reports_dir: Path,
    figures_dir: Path,
) -> dict[str, Path]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_paths = {
        "inventory_report": reports_dir / "inventory_report.md",
        "inventory_business_summary": reports_dir / "inventory_business_summary.md",
        "inventory_cost_analysis": reports_dir / "inventory_cost_analysis.md",
        "inventory_risk_report": reports_dir / "inventory_risk_report.md",
        "inventory_recommendation_report": reports_dir / "inventory_recommendation_report.md",
        "executive_inventory_report": reports_dir / "executive_inventory_report.md",
    }

    top_cost = inventory_metrics.sort_values("TotalInventoryCost", ascending=False).head(10)
    top_risk = inventory_risk.sort_values("InventoryRiskScore", ascending=False).head(10)
    top_recommendations = inventory_recommendations.head(20)
    top_dashboard = inventory_dashboard.head(20)
    top_health = inventory_metrics.sort_values("InventoryHealthScore", ascending=False).head(10)

    write_text(
        f"""# Inventory Report

## Overview
RetailPulse Phase 4 converts the enterprise forecasting outputs into an inventory optimization engine covering replenishment policy, cost optimization, risk detection, and operational recommendation generation.

## Dependency Status
{dependency_status_markdown()}

## Best Inventory Risk Model
- Selected model: **{best_model_payload.get('model_name', 'Unavailable')}**
- F1 score: **{best_model_payload.get('metrics', {}).get('f1', float('nan')):.4f}**
- ROC-AUC: **{best_model_payload.get('metrics', {}).get('roc_auc', float('nan')):.4f}**

## Inventory Formulas
- **Safety Stock**: z-score driven service buffer using demand and lead-time variability.
- **Reorder Point**: average daily demand over supplier lead time plus safety stock.
- **EOQ**: square-root cost trade-off between ordering cost and carrying cost.
- **Inventory Health Score**: blended score balancing risk, service, and turnover.

## Inventory Dataset Snapshot
{frame_to_markdown_like(inventory_dataset, rows=12)}

## Inventory Metrics Snapshot
{frame_to_markdown_like(inventory_metrics, rows=12)}

## ML Evaluation
{frame_to_markdown_like(model_metrics, rows=12)}

## Visual Assets
Inventory figures are available under `{figures_dir}`.
""",
        report_paths["inventory_report"],
    )

    write_text(
        f"""# Inventory Business Summary

## Horizon Dashboard
{frame_to_markdown_like(top_dashboard, rows=20)}

## Healthiest Inventory Positions
{frame_to_markdown_like(top_health, rows=10)}

## Revenue Protection Priorities
{frame_to_markdown_like(inventory_metrics.sort_values('PotentialRevenueLoss', ascending=False), rows=10)}
""",
        report_paths["inventory_business_summary"],
    )

    write_text(
        f"""# Inventory Cost Analysis

## Highest Cost Exposures
{frame_to_markdown_like(top_cost, rows=12)}

## Cost Optimization Summary
Total projected inventory cost: **{inventory_metrics['TotalInventoryCost'].sum():,.2f}**

Total optimized inventory cost: **{inventory_metrics['OptimizedInventoryCost'].sum():,.2f}**

Inventory savings opportunity: **{inventory_metrics['InventorySavings'].sum():,.2f}**

Expected profit improvement: **{inventory_metrics['ExpectedProfitImprovement'].sum():,.2f}**
""",
        report_paths["inventory_cost_analysis"],
    )

    write_text(
        f"""# Inventory Risk Report

## Highest Risk Items
{frame_to_markdown_like(top_risk, rows=12)}

## Risk Model Comparison
{frame_to_markdown_like(model_metrics, rows=12)}

## Risk Interpretation
- Stockout risk rises when projected stock falls below reorder point and coverage drops under supplier lead time.
- Overstock risk increases when inventory coverage materially exceeds the demand window.
- Demand spike risk reflects widening gaps between base forecast and upper confidence interval.
- Supplier delay risk captures long and volatile replenishment lanes.
- Inventory age risk highlights slow-moving or dead-stock behavior.
""",
        report_paths["inventory_risk_report"],
    )

    write_text(
        f"""# Inventory Recommendation Report

## Recommended Actions
{frame_to_markdown_like(top_recommendations, rows=25)}
""",
        report_paths["inventory_recommendation_report"],
    )

    write_text(
        f"""# Executive Inventory Report

The RetailPulse inventory engine converted demand forecasts into replenishment and cost decisions across SKU, category, country, and warehouse views.

Key takeaways:
- Best risk classifier: **{best_model_payload.get('model_name', 'Unavailable')}**
- Inventory savings opportunity: **{inventory_metrics['InventorySavings'].sum():,.2f}**
- Potential revenue at risk: **{inventory_metrics['PotentialRevenueLoss'].sum():,.2f}**
- Highest risk horizon is visible in the dashboard output and risk report.
- Operational recommendations are prioritized across reorder, stock reduction, sourcing, and transfer actions.
""",
        report_paths["executive_inventory_report"],
    )
    return report_paths


def write_inventory_notebook(notebooks_dir: Path) -> Path:
    notebooks_dir.mkdir(parents=True, exist_ok=True)
    notebook_path = notebooks_dir / "05_inventory_optimization.ipynb"
    notebook = {
        "cells": [
            make_notebook_cell(
                "markdown",
                """
# RetailPulse Phase 4: Enterprise Inventory Optimization

This notebook documents the Phase 4 workflow that converts RetailPulse demand forecasts into inventory planning, optimization, risk scoring, and business recommendations.

## Coverage

- Inventory-ready dataset engineering
- ABC, XYZ, and ABC-XYZ inventory analytics
- Stockout, overstock, demand spike, supplier delay, and inventory age risk detection
- EOQ, reorder point, safety stock, lead-time, and cost optimization
- Inventory risk model benchmarking with graceful fallbacks when class diversity is limited
- Executive-ready metrics, reports, dashboards, and figures
                """,
            ),
            make_notebook_cell(
                "markdown",
                """
## Inventory Formulas

- **Safety Stock** = z-score service buffer using demand variability and lead-time variability
- **Reorder Point** = average daily demand x supplier lead time + safety stock
- **Economic Order Quantity (EOQ)** = sqrt((2 x annual demand x ordering cost) / carrying cost)
- **Stock Coverage Days** = estimated stock / daily demand
- **Inventory Health Score** = blended service, turnover, and risk balance score

## Business Logic

- Increase stock when projected coverage drops below supplier lead time
- Reduce or delay purchases when coverage becomes excessive
- Escalate supplier review when variability and delay risk remain elevated
- Prioritize dead-stock and discount actions when turnover decays and age risk rises
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

from inventory_optimization import run_inventory_optimization
                """,
            ),
            make_notebook_cell(
                "code",
                """
result = run_inventory_optimization(
    dataset_path=PROJECT_ROOT / "data" / "processed" / "final_processed_dataset.csv",
    forecast_path=PROJECT_ROOT / "processed" / "future_predictions.csv",
    output_dir=PROJECT_ROOT / "processed",
    reports_dir=PROJECT_ROOT / "reports",
    figures_dir=PROJECT_ROOT / "reports" / "figures",
    models_dir=PROJECT_ROOT / "models",
)

result["best_model_name"], len(result["visual_paths"])
                """,
            ),
            make_notebook_cell(
                "code",
                """
inventory_metrics = pd.read_csv(PROJECT_ROOT / "processed" / "inventory_metrics.csv")
inventory_risk = pd.read_csv(PROJECT_ROOT / "processed" / "inventory_risk.csv")
inventory_recommendations = pd.read_csv(PROJECT_ROOT / "processed" / "inventory_recommendations.csv")
inventory_dashboard = pd.read_csv(PROJECT_ROOT / "processed" / "inventory_dashboard.csv")
model_metrics = result["model_metrics"]

inventory_metrics.head()
                """,
            ),
            make_notebook_cell(
                "markdown",
                """
## Machine Learning Evaluation

Use the model comparison frame to review:

- Accuracy
- Precision
- Recall
- F1 score
- ROC-AUC
- Confusion matrix

Optional libraries such as XGBoost, LightGBM, and CatBoost are skipped automatically when they are unavailable.
                """,
            ),
            make_notebook_cell(
                "code",
                """
model_metrics.sort_values(["f1", "roc_auc", "accuracy"], ascending=False)
                """,
            ),
            make_notebook_cell(
                "code",
                """
inventory_recommendations.head(15)
                """,
            ),
            make_notebook_cell(
                "markdown",
                """
## Executive Insights

- Review the horizon KPI dashboard for cost, savings, and risk trade-offs by forecast window
- Focus on high-risk SKUs where revenue exposure and supplier lead times are both elevated
- Use the recommendation table to separate urgent replenishment from cost-reduction actions
- Validate warehouse allocation, dead-stock exposure, and service-level posture before procurement release
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


def run_inventory_optimization(
    dataset_path: str | Path | None = None,
    forecast_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    reports_dir: str | Path | None = None,
    figures_dir: str | Path | None = None,
    models_dir: str | Path | None = None,
) -> dict[str, Any]:
    logger.info("Running RetailPulse Phase 4 inventory optimization workflow")
    project_root = Path(__file__).resolve().parents[1]
    dataset_path = Path(dataset_path) if dataset_path is not None else FINAL_PROCESSED_DATA_PATH
    forecast_path = Path(forecast_path) if forecast_path is not None else project_root / "processed" / "future_predictions.csv"

    if not dataset_path.exists():
        raise FileNotFoundError(f"Processed retail dataset not found at {dataset_path}")
    if not forecast_path.exists():
        raise FileNotFoundError(f"Forecast output not found at {forecast_path}")

    raw_df, sku_forecasts = load_inventory_sources(dataset_path, forecast_path)
    history_df = build_inventory_history(raw_df, sku_forecasts)
    summary_df, abc_analysis, xyz_analysis, abc_xyz_matrix = compute_abc_xyz(history_df)
    inventory_dataset = simulate_inventory_dataset(summary_df, sku_forecasts)
    model_metrics, best_model_payload, prediction_frame = train_inventory_risk_models(inventory_dataset)
    inventory_dataset = enrich_with_model_predictions(inventory_dataset, prediction_frame)
    inventory_metrics = summarize_inventory_metrics(inventory_dataset)
    inventory_risk = summarize_inventory_risk(inventory_dataset)
    inventory_recommendations = create_inventory_recommendations(inventory_metrics)
    inventory_dashboard = create_inventory_dashboard(inventory_dataset, inventory_metrics, inventory_risk, inventory_recommendations)

    output_path = Path(output_dir) if output_dir is not None else project_root / "processed"
    reports_path = Path(reports_dir) if reports_dir is not None else project_root / "reports"
    figures_path = Path(figures_dir) if figures_dir is not None else reports_path / "figures"
    models_path = Path(models_dir) if models_dir is not None else project_root / "models"

    visual_paths = create_inventory_visualizations(
        dataset=inventory_dataset,
        metrics=inventory_metrics,
        risk_summary=inventory_risk,
        dashboard=inventory_dashboard,
        recommendations=inventory_recommendations,
        abc_analysis=abc_analysis,
        xyz_analysis=xyz_analysis,
        abc_xyz_matrix=abc_xyz_matrix,
        model_metrics=model_metrics,
        figures_dir=figures_path,
    )
    artifact_paths = save_inventory_artifacts(
        inventory_dataset=inventory_dataset,
        inventory_metrics=inventory_metrics,
        inventory_risk=inventory_risk,
        inventory_dashboard=inventory_dashboard,
        inventory_recommendations=inventory_recommendations,
        abc_analysis=abc_analysis,
        xyz_analysis=xyz_analysis,
        abc_xyz_matrix=abc_xyz_matrix,
        best_model_payload=best_model_payload,
        model_metrics=model_metrics,
        output_dir=output_path,
        models_dir=models_path,
    )
    report_paths = write_inventory_reports(
        inventory_dataset=inventory_dataset,
        inventory_metrics=inventory_metrics,
        inventory_risk=inventory_risk,
        inventory_dashboard=inventory_dashboard,
        inventory_recommendations=inventory_recommendations,
        model_metrics=model_metrics,
        best_model_payload=best_model_payload,
        reports_dir=reports_path,
        figures_dir=figures_path,
    )
    notebook_path = write_inventory_notebook(project_root / "notebooks")

    try:
        from mlflow_utils import SafeMLflowRun, log_parameter, log_metric, log_artifact
        with SafeMLflowRun("RetailPulse Inventory Optimization", "inventory_optimization_run"):
            best_model_name = best_model_payload.get("model_name", "Unavailable")
            log_parameter("best_model_name", best_model_name)
            
            if model_metrics is not None and not model_metrics.empty:
                for _, row in model_metrics.iterrows():
                    m_name = str(row["model_name"]).replace(" ", "_")
                    log_metric(f"inventory_{m_name}_accuracy", row.get("accuracy", 0.0))
                    log_metric(f"inventory_{m_name}_precision", row.get("precision", 0.0))
                    log_metric(f"inventory_{m_name}_recall", row.get("recall", 0.0))
                    log_metric(f"inventory_{m_name}_f1", row.get("f1", 0.0))
                    log_metric(f"inventory_{m_name}_roc_auc", row.get("roc_auc", 0.0))
                    
            for path in artifact_paths.values():
                log_artifact(path, "csv_outputs")
            for path in report_paths.values():
                log_artifact(path, "reports")
            for path in visual_paths:
                log_artifact(path, "plots")
            if notebook_path:
                log_artifact(notebook_path, "notebooks")
    except Exception as e:
        logger.warning(f"Failed to log Phase 4 inventory run to MLflow: {e}")

    return {
        "inventory_dataset": inventory_dataset,
        "inventory_metrics": inventory_metrics,
        "inventory_risk": inventory_risk,
        "inventory_dashboard": inventory_dashboard,
        "inventory_recommendations": inventory_recommendations,
        "abc_analysis": abc_analysis,
        "xyz_analysis": xyz_analysis,
        "abc_xyz_matrix": abc_xyz_matrix,
        "model_metrics": model_metrics,
        "best_model_name": best_model_payload.get("model_name", "Unavailable"),
        "artifact_paths": artifact_paths,
        "report_paths": report_paths,
        "visual_paths": visual_paths,
        "notebook_path": notebook_path,
    }
