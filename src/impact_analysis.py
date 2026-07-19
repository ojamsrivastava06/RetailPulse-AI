from __future__ import annotations

import pandas as pd

from decision_utils import numeric_series, safe_divide


FINANCIAL_COLUMNS = [
    "RevenueOpportunity",
    "CostReduction",
    "InventorySavings",
    "RetentionGain",
    "ProfitImprovement",
]


def attach_financial_impact(decisions: pd.DataFrame) -> pd.DataFrame:
    if decisions.empty:
        return decisions.copy()

    data = decisions.copy()
    for column in FINANCIAL_COLUMNS:
        if column not in data.columns:
            data[column] = 0.0
        data[column] = numeric_series(data, column)

    data["FinancialImpact"] = data[FINANCIAL_COLUMNS].sum(axis=1).round(2)
    data["ImplementationCost"] = (
        data["FinancialImpact"].abs() * 0.08
        + data["BusinessRiskScore"].fillna(0).astype(float) * 12.5
        + 250
    ).round(2)
    high_touch = data["DecisionType"].astype(str).str.contains("Customer|Promotion|Supplier", case=False, regex=True)
    data.loc[high_touch, "ImplementationCost"] = (data.loc[high_touch, "ImplementationCost"] * 1.18).round(2)
    data["ExpectedROI"] = (
        safe_divide(data["FinancialImpact"] - data["ImplementationCost"], data["ImplementationCost"], default=0.0) * 100
    ).round(2)
    data["BusinessImpact"] = data["FinancialImpact"].map(
        lambda value: "High" if value >= 25_000 else "Medium" if value >= 5_000 else "Targeted"
    )
    return data


def build_roi_summary(decisions: pd.DataFrame) -> pd.DataFrame:
    if decisions.empty:
        return pd.DataFrame(
            columns=[
                "Domain",
                "Recommendations",
                "RevenueGain",
                "CostReduction",
                "InventorySavings",
                "RetentionGain",
                "ProfitImprovement",
                "FinancialImpact",
                "ExpectedROI",
            ]
        )

    data = attach_financial_impact(decisions)
    summary = (
        data.groupby("Domain", dropna=False)
        .agg(
            Recommendations=("DecisionID", "count"),
            RevenueGain=("RevenueOpportunity", "sum"),
            CostReduction=("CostReduction", "sum"),
            InventorySavings=("InventorySavings", "sum"),
            RetentionGain=("RetentionGain", "sum"),
            ProfitImprovement=("ProfitImprovement", "sum"),
            FinancialImpact=("FinancialImpact", "sum"),
            ExpectedROI=("ExpectedROI", "mean"),
        )
        .reset_index()
    )
    return summary.round(2)
