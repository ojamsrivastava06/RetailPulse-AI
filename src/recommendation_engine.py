from __future__ import annotations

import pandas as pd

from confidence_engine import attach_confidence_scores
from decision_models import DecisionConfig
from decision_utils import add_decision_ids, normalize_score, priority_level, time_sensitivity
from impact_analysis import attach_financial_impact
from risk_engine import attach_risk_scores


def score_recommendations(
    decisions: pd.DataFrame,
    forecast_comparison: pd.DataFrame,
    customer_leaderboard: pd.DataFrame,
    inventory_dashboard: pd.DataFrame,
    config: DecisionConfig,
) -> pd.DataFrame:
    if decisions.empty:
        return decisions.copy()

    data = attach_risk_scores(decisions)
    data["ImpactScore"] = normalize_score(
        data[["RevenueOpportunity", "CostReduction", "InventorySavings", "RetentionGain", "ProfitImprovement"]].sum(axis=1)
    )
    data = attach_financial_impact(data)
    data = attach_confidence_scores(data, forecast_comparison, customer_leaderboard, inventory_dashboard)

    weights = config.priority_weights
    data["PriorityScore"] = (
        data["ImpactScore"] * weights["financial"]
        + data["BusinessRiskScore"] * weights["risk"]
        + data["Confidence"] * weights["confidence"]
        + data["UrgencyScore"] * weights["urgency"]
    ).clip(0, 100).round(2)
    data["PriorityBand"] = data["PriorityScore"].map(priority_level)
    data["TimeSensitivity"] = data["PriorityScore"].map(time_sensitivity)
    data = add_decision_ids(data.sort_values("PriorityScore", ascending=False))
    return data


def build_priority_actions(scored_decisions: pd.DataFrame, limit: int = 50) -> pd.DataFrame:
    if scored_decisions.empty:
        return pd.DataFrame()
    columns = [
        "DecisionID",
        "PriorityBand",
        "PriorityScore",
        "DecisionType",
        "Domain",
        "Entity",
        "BusinessImpact",
        "FinancialImpact",
        "ExpectedROI",
        "RiskLevel",
        "Confidence",
        "TimeSensitivity",
        "SuggestedAction",
        "Reasoning",
    ]
    return scored_decisions[[column for column in columns if column in scored_decisions.columns]].head(limit).copy()


def build_business_alerts(scored_decisions: pd.DataFrame) -> pd.DataFrame:
    if scored_decisions.empty:
        return pd.DataFrame(
            columns=["AlertID", "AlertType", "Severity", "Domain", "Entity", "Message", "RecommendedAction", "PriorityScore"]
        )

    high = scored_decisions[
        (scored_decisions["PriorityScore"] >= 40)
        | scored_decisions["RiskLevel"].isin(["Critical", "High", "Medium"])
    ].copy()
    if len(high) < 25:
        high = (
            pd.concat([high, scored_decisions.head(50)], ignore_index=True)
            .drop_duplicates("DecisionID")
            .head(50)
            .copy()
        )

    alert_type = high["DecisionType"].map(_alert_type)
    severity = high.apply(_alert_severity, axis=1)
    alerts = pd.DataFrame(
        {
            "AlertID": [f"AL-{index + 1:05d}" for index in range(len(high))],
            "AlertType": alert_type,
            "Severity": severity,
            "Domain": high["Domain"],
            "Entity": high["Entity"],
            "Message": high.apply(
                lambda row: f"{row['DecisionType']} recommended for {row['Entity']} with priority {row['PriorityScore']:.1f}.",
                axis=1,
            ),
            "RecommendedAction": high["SuggestedAction"],
            "PriorityScore": high["PriorityScore"],
            "RiskLevel": high["RiskLevel"],
            "FinancialImpact": high["FinancialImpact"],
            "TimeSensitivity": high["TimeSensitivity"],
            "DecisionID": high["DecisionID"],
        }
    )
    severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Watch": 3}
    alerts["_SeverityOrder"] = alerts["Severity"].map(severity_order).fillna(9)
    return (
        alerts.sort_values(["_SeverityOrder", "PriorityScore"], ascending=[True, False])
        .drop(columns=["_SeverityOrder"])
        .reset_index(drop=True)
    )


def _alert_severity(row: pd.Series) -> str:
    if row.get("RiskLevel") == "Critical" or float(row.get("PriorityScore", 0.0)) >= 85:
        return "Critical"
    if row.get("RiskLevel") == "High" or float(row.get("PriorityScore", 0.0)) >= 70:
        return "High"
    if row.get("RiskLevel") == "Medium" or float(row.get("PriorityScore", 0.0)) >= 45:
        return "Medium"
    return "Watch"


def _alert_type(decision_type: str) -> str:
    mapping = {
        "Restock SKU": "Stockout Expected",
        "Increase Inventory": "Demand Spike",
        "Increase Safety Stock": "High Stock Risk",
        "Reduce Overstock": "Inventory Excess",
        "Supplier Escalation": "Supplier Delay",
        "Warehouse Transfer": "Inventory Shortage",
        "Retain High Value Customer": "Customer Leaving",
        "Launch Promotion": "Revenue Opportunity",
        "Bundle Products": "Revenue Opportunity",
        "Stop Low Demand Items": "Forecast Drop",
        "Decrease Inventory": "Inventory Excess",
        "Upsell Premium Products": "Revenue Opportunity",
    }
    return mapping.get(str(decision_type), "Business Alert")
