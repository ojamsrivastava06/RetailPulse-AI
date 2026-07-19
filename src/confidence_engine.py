from __future__ import annotations

import pandas as pd

from decision_utils import clip_score, numeric_series


def _forecast_accuracy(forecast_comparison: pd.DataFrame) -> float:
    if forecast_comparison.empty or "mape" not in forecast_comparison.columns:
        return 72.0
    mape = pd.to_numeric(forecast_comparison["mape"], errors="coerce").dropna()
    if mape.empty:
        return 72.0
    return float(max(0.0, min(100.0, (1.0 - float(mape.min())) * 100)))


def _churn_confidence(customer_leaderboard: pd.DataFrame) -> float:
    if customer_leaderboard.empty:
        return 70.0
    candidate_columns = [column for column in ["f1", "balanced_accuracy", "roc_auc"] if column in customer_leaderboard.columns]
    if not candidate_columns:
        return 70.0
    metrics = customer_leaderboard[candidate_columns].apply(pd.to_numeric, errors="coerce")
    return float(metrics.max(axis=1).max() * 100)


def _inventory_confidence(inventory_dashboard: pd.DataFrame) -> float:
    if inventory_dashboard.empty or "InventoryHealthScore" not in inventory_dashboard.columns:
        return 74.0
    health = pd.to_numeric(inventory_dashboard["InventoryHealthScore"], errors="coerce").dropna()
    if health.empty:
        return 74.0
    return float(health.mean())


def confidence_baselines(
    forecast_comparison: pd.DataFrame,
    customer_leaderboard: pd.DataFrame,
    inventory_dashboard: pd.DataFrame,
) -> dict[str, float]:
    forecast = _forecast_accuracy(forecast_comparison)
    inventory = _inventory_confidence(inventory_dashboard)
    customer = _churn_confidence(customer_leaderboard)
    return {
        "Forecasting": forecast,
        "Inventory": inventory,
        "Customer": customer,
        "Churn": customer,
        "Executive": (forecast + inventory + customer) / 3,
    }


def attach_confidence_scores(
    decisions: pd.DataFrame,
    forecast_comparison: pd.DataFrame,
    customer_leaderboard: pd.DataFrame,
    inventory_dashboard: pd.DataFrame,
) -> pd.DataFrame:
    if decisions.empty:
        return decisions.copy()

    data = decisions.copy()
    baselines = confidence_baselines(forecast_comparison, customer_leaderboard, inventory_dashboard)
    data["ModelConfidence"] = data["Domain"].map(baselines).fillna(baselines["Executive"]).astype(float)
    data["HistoricalAccuracy"] = data["ModelConfidence"]
    data["BusinessConfidence"] = (
        100
        - numeric_series(data, "BusinessRiskScore") * 0.28
        + numeric_series(data, "UrgencyScore") * 0.10
        + numeric_series(data, "ImpactScore") * 0.12
    )
    data["BusinessConfidence"] = clip_score(data["BusinessConfidence"])
    data["RecommendationReliability"] = (
        data["ModelConfidence"] * 0.42
        + data["HistoricalAccuracy"] * 0.22
        + data["BusinessConfidence"] * 0.36
    ).round(2)
    data["Confidence"] = data["RecommendationReliability"].round(2)
    return data
