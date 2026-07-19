from __future__ import annotations

import pandas as pd

from decision_models import DecisionConfig
from decision_utils import numeric_series, risk_level


def build_scenario_analysis(
    future_predictions: pd.DataFrame,
    inventory_dashboard: pd.DataFrame,
    churn_predictions: pd.DataFrame,
    config: DecisionConfig,
) -> pd.DataFrame:
    baseline_revenue = float(numeric_series(future_predictions, "ForecastRevenue").sum())
    baseline_demand = float(numeric_series(future_predictions, "ForecastDemand").sum())
    inventory_cost = float(numeric_series(inventory_dashboard, "TotalInventoryCost").sum())
    inventory_savings = float(numeric_series(inventory_dashboard, "InventorySavings").sum())
    potential_loss = float(numeric_series(inventory_dashboard, "PotentialRevenueLoss").sum())
    churn_value_at_risk = float(
        (
            numeric_series(churn_predictions, "ExpectedLifetimeValue")
            * numeric_series(churn_predictions, "ChurnProbability")
        ).sum()
    )

    rows: list[dict[str, float | str]] = []
    for name, params in config.scenario_definitions.items():
        demand_shift = float(params["demand"])
        price_shift = float(params["price"])
        supplier_shift = float(params["supplier"])
        churn_shift = float(params["churn"])

        expected_revenue = baseline_revenue * (1 + demand_shift) * (1 + price_shift)
        revenue_impact = expected_revenue - baseline_revenue
        expected_demand = baseline_demand * (1 + demand_shift)
        inventory_impact = inventory_cost * abs(demand_shift) * 0.22 + potential_loss * max(demand_shift, 0) * 0.18
        supplier_impact = potential_loss * supplier_shift * 0.55
        churn_impact = churn_value_at_risk * churn_shift
        savings_impact = inventory_savings * (0.08 + max(-demand_shift, 0) * 0.15)
        profit_impact = revenue_impact * 0.18 - inventory_impact - supplier_impact - max(churn_impact, 0) + savings_impact
        risk_score = min(
            100.0,
            35
            + abs(demand_shift) * 120
            + max(supplier_shift, 0) * 150
            + max(churn_shift, 0) * 130
            + max(-price_shift, 0) * 60,
        )

        rows.append(
            {
                "Scenario": name,
                "DemandShift": demand_shift,
                "PriceShift": price_shift,
                "SupplierDelayFactor": supplier_shift,
                "ChurnShift": churn_shift,
                "ExpectedDemand": round(expected_demand, 2),
                "ExpectedRevenue": round(expected_revenue, 2),
                "RevenueImpact": round(revenue_impact, 2),
                "InventoryImpact": round(inventory_impact, 2),
                "SupplierImpact": round(supplier_impact, 2),
                "ChurnImpact": round(churn_impact, 2),
                "ProfitImpact": round(profit_impact, 2),
                "RiskScore": round(risk_score, 2),
                "RiskLevel": risk_level(risk_score),
                "RecommendedResponse": _scenario_response(name, revenue_impact, risk_score),
            }
        )

    return pd.DataFrame(rows)


def _scenario_response(name: str, revenue_impact: float, risk_score: float) -> str:
    if "Supplier" in name:
        return "Escalate critical suppliers, confirm lead times, and protect high-revenue SKUs."
    if "Shortage" in name:
        return "Prioritize replenishment, safety stock, and warehouse transfer decisions."
    if "Churn" in name:
        return "Fund retention actions for high-value customers and monitor weekly risk movement."
    if "Discount" in name:
        return "Use margin guardrails and target discounts to slow-moving or bundle-ready products."
    if "Increase" in name:
        return "Validate price elasticity and protect demand-sensitive customer segments."
    if revenue_impact > 0 and risk_score >= 65:
        return "Capture revenue upside while pre-allocating inventory and fulfillment capacity."
    if revenue_impact < 0:
        return "Reduce exposure, preserve cash, and focus promotions on recoverable demand."
    return "Monitor scenario indicators and keep current operating plan active."
