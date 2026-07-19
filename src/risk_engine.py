from __future__ import annotations

import pandas as pd

from decision_utils import clip_score, numeric_series, risk_level


RISK_COLUMNS = [
    "ForecastRisk",
    "InventoryRisk",
    "CustomerRisk",
    "RevenueRisk",
    "SupplierRisk",
    "OperationalRisk",
]


def attach_risk_scores(decisions: pd.DataFrame) -> pd.DataFrame:
    if decisions.empty:
        return decisions.copy()

    data = decisions.copy()
    for column in RISK_COLUMNS:
        if column not in data.columns:
            data[column] = 0.0

    data["ForecastRisk"] = clip_score(numeric_series(data, "ForecastRisk"))
    data["InventoryRisk"] = clip_score(numeric_series(data, "InventoryRisk"))
    data["CustomerRisk"] = clip_score(numeric_series(data, "CustomerRisk"))
    data["RevenueRisk"] = clip_score(numeric_series(data, "RevenueRisk"))
    data["SupplierRisk"] = clip_score(numeric_series(data, "SupplierRisk"))
    data["OperationalRisk"] = clip_score(numeric_series(data, "OperationalRisk"))

    data["BusinessRiskScore"] = (
        data["ForecastRisk"] * 0.18
        + data["InventoryRisk"] * 0.24
        + data["CustomerRisk"] * 0.18
        + data["RevenueRisk"] * 0.18
        + data["SupplierRisk"] * 0.10
        + data["OperationalRisk"] * 0.12
    ).round(2)
    data["RiskLevel"] = data["BusinessRiskScore"].map(risk_level)
    return data


def build_risk_summary(decisions: pd.DataFrame, inventory_dashboard: pd.DataFrame, churn: pd.DataFrame) -> pd.DataFrame:
    if decisions.empty:
        return pd.DataFrame(
            columns=[
                "RiskDomain",
                "RiskScore",
                "RiskLevel",
                "Drivers",
                "RecommendedMitigation",
            ]
        )

    data = attach_risk_scores(decisions)
    inventory_score = (
        pd.to_numeric(inventory_dashboard.get("InventoryRiskScore", pd.Series(dtype=float)), errors="coerce")
        .fillna(0.0)
        .mean()
    )
    churn_score = (
        pd.to_numeric(churn.get("ChurnProbability", pd.Series(dtype=float)), errors="coerce")
        .fillna(0.0)
        .mean()
        * 100
    )

    rows = [
        {
            "RiskDomain": "Forecast Risk",
            "RiskScore": round(float(data["ForecastRisk"].mean()), 2),
            "Drivers": "Demand variance, forecast error, and revenue concentration.",
            "RecommendedMitigation": "Review high-error series and validate near-term replenishment assumptions.",
        },
        {
            "RiskDomain": "Inventory Risk",
            "RiskScore": round(max(float(data["InventoryRisk"].mean()), float(inventory_score)), 2),
            "Drivers": "Stockout exposure, overstock exposure, coverage days, and reorder pressure.",
            "RecommendedMitigation": "Prioritize P0/P1 replenishment, safety stock, and warehouse transfer actions.",
        },
        {
            "RiskDomain": "Customer Risk",
            "RiskScore": round(max(float(data["CustomerRisk"].mean()), float(churn_score)), 2),
            "Drivers": "Churn probability, customer health, lifetime value at risk, and engagement drop.",
            "RecommendedMitigation": "Launch retention actions for high-value critical-risk customers.",
        },
        {
            "RiskDomain": "Revenue Risk",
            "RiskScore": round(float(data["RevenueRisk"].mean()), 2),
            "Drivers": "Revenue at risk from demand drop, stockouts, churn, and low product velocity.",
            "RecommendedMitigation": "Protect top revenue drivers and rebalance promotion focus.",
        },
        {
            "RiskDomain": "Supplier Risk",
            "RiskScore": round(float(data["SupplierRisk"].mean()), 2),
            "Drivers": "Lead-time pressure, supplier delay risk, and fulfillment constraints.",
            "RecommendedMitigation": "Escalate supplier lanes tied to critical SKUs and high revenue exposure.",
        },
        {
            "RiskDomain": "Operational Risk",
            "RiskScore": round(float(data["OperationalRisk"].mean()), 2),
            "Drivers": "Warehouse allocation, fulfillment readiness, action urgency, and execution complexity.",
            "RecommendedMitigation": "Assign owners for immediate actions and track weekly closure.",
        },
    ]
    summary = pd.DataFrame(rows)
    summary["RiskScore"] = summary["RiskScore"].clip(0, 100)
    summary["RiskLevel"] = summary["RiskScore"].map(risk_level)
    return summary[["RiskDomain", "RiskScore", "RiskLevel", "Drivers", "RecommendedMitigation"]]
