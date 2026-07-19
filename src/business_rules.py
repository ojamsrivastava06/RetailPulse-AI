from __future__ import annotations

import numpy as np
import pandas as pd

from decision_models import DecisionConfig
from decision_utils import coalesce_numeric, coalesce_text, normalize_score, numeric_series, text_series, top_n


DECISION_COLUMNS = [
    "Domain",
    "DecisionType",
    "EntityType",
    "Entity",
    "Product",
    "Country",
    "ProductCategory",
    "Warehouse",
    "BusinessImpact",
    "RevenueOpportunity",
    "CostReduction",
    "InventorySavings",
    "RetentionGain",
    "ProfitImprovement",
    "ForecastRisk",
    "InventoryRisk",
    "CustomerRisk",
    "RevenueRisk",
    "SupplierRisk",
    "OperationalRisk",
    "UrgencyScore",
    "Reasoning",
    "SuggestedAction",
    "SourcePhase",
    "SourceArtifact",
]


def _empty_decisions() -> pd.DataFrame:
    return pd.DataFrame(columns=DECISION_COLUMNS)


def _standardize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return _empty_decisions()
    data = frame.copy()
    for column in DECISION_COLUMNS:
        if column not in data.columns:
            data[column] = 0.0 if column.endswith(("Risk", "Score", "Impact")) else ""
    return data[DECISION_COLUMNS]


def build_forecast_decisions(
    future_predictions: pd.DataFrame,
    forecast_comparison: pd.DataFrame,
    config: DecisionConfig,
) -> pd.DataFrame:
    if future_predictions.empty:
        return _empty_decisions()

    data = future_predictions.copy()
    data["ForecastRevenue"] = numeric_series(data, "ForecastRevenue")
    data["ForecastDemand"] = numeric_series(data, "ForecastDemand")
    data["Uncertainty"] = (
        coalesce_numeric(data, ["Upper95Demand"], 0.0) - coalesce_numeric(data, ["Lower95Demand"], 0.0)
    ).clip(lower=0)
    data["UncertaintyRatio"] = data["Uncertainty"] / data["ForecastDemand"].replace(0, np.nan)
    data["UncertaintyRatio"] = data["UncertaintyRatio"].replace([np.inf, -np.inf], np.nan).fillna(0.0)

    high_value = top_n(data[data["ForecastRevenue"] > 0], ["ForecastRevenue", "ForecastDemand"], config.max_forecast_decisions)
    if high_value.empty:
        return _empty_decisions()

    low_threshold = data["ForecastDemand"].quantile(0.15) if len(data) else 0
    low_demand = data[data["ForecastDemand"] <= low_threshold].sort_values("ForecastRevenue").head(20)
    combined = pd.concat([high_value, low_demand], ignore_index=True).drop_duplicates(
        subset=[column for column in ["SeriesKey", "Product", "Country", "ProductCategory", "Date"] if column in data.columns]
    )

    revenue_score = normalize_score(combined["ForecastRevenue"])
    uncertainty_score = normalize_score(combined["UncertaintyRatio"])
    low_demand_mask = combined["ForecastDemand"] <= low_threshold
    decision_type = np.select(
        [
            low_demand_mask,
            combined["ForecastDemand"] >= combined["ForecastDemand"].quantile(0.75),
            combined["ForecastRevenue"] >= combined["ForecastRevenue"].quantile(0.75),
        ],
        ["Stop Low Demand Items", "Increase Inventory", "Launch Promotion"],
        default="Bundle Products",
    )

    forecast_error = 18.0
    if not forecast_comparison.empty and "mape" in forecast_comparison.columns:
        forecast_error = float(pd.to_numeric(forecast_comparison["mape"], errors="coerce").min() * 100)

    out = pd.DataFrame(
        {
            "Domain": "Forecasting",
            "DecisionType": decision_type,
            "EntityType": coalesce_text(combined, ["ForecastLevel"], "SKU Forecast"),
            "Entity": coalesce_text(combined, ["Entity", "Product", "SeriesKey"], "Forecast series"),
            "Product": coalesce_text(combined, ["Product"], ""),
            "Country": coalesce_text(combined, ["Country"], ""),
            "ProductCategory": coalesce_text(combined, ["ProductCategory"], ""),
            "Warehouse": "",
            "BusinessImpact": "High",
            "RevenueOpportunity": combined["ForecastRevenue"] * np.where(low_demand_mask, 0.03, 0.12),
            "CostReduction": np.where(low_demand_mask, combined["ForecastRevenue"].abs() * 0.04, 0.0),
            "InventorySavings": 0.0,
            "RetentionGain": 0.0,
            "ProfitImprovement": combined["ForecastRevenue"] * np.where(low_demand_mask, 0.02, 0.05),
            "ForecastRisk": (forecast_error + uncertainty_score * 0.55).clip(0, 100),
            "InventoryRisk": np.where(decision_type == "Increase Inventory", revenue_score * 0.55, 20.0),
            "CustomerRisk": 0.0,
            "RevenueRisk": revenue_score,
            "SupplierRisk": 0.0,
            "OperationalRisk": np.where(low_demand_mask, 35.0, 55.0),
            "UrgencyScore": np.where(low_demand_mask, 45.0, revenue_score * 0.72 + uncertainty_score * 0.28),
            "Reasoning": np.where(
                low_demand_mask,
                "Forecast demand is in the lowest band; reduce exposure or test targeted demand creation.",
                "Forecasted demand and revenue justify proactive commercial and inventory action.",
            ),
            "SuggestedAction": np.where(
                low_demand_mask,
                "Review assortment, pause replenishment, and validate promotional fit.",
                "Align inventory, pricing, and promotion planning to capture forecasted demand.",
            ),
            "SourcePhase": "Phase 3 - Enterprise Demand Forecasting",
            "SourceArtifact": "future_predictions.csv",
        }
    )
    return _standardize(out)


def build_inventory_decisions(
    inventory_recommendations: pd.DataFrame,
    inventory_metrics: pd.DataFrame,
    inventory_risk: pd.DataFrame,
    config: DecisionConfig,
) -> pd.DataFrame:
    if inventory_recommendations.empty and inventory_metrics.empty and inventory_risk.empty:
        return _empty_decisions()

    base = inventory_recommendations.copy()
    join_keys = [key for key in ["SeriesKey", "Product", "Country", "ProductCategory", "HorizonDays"] if key in base.columns]
    if not base.empty and join_keys:
        metric_columns = [
            column
            for column in [
                *join_keys,
                "Warehouse",
                "ForecastRevenue",
                "ForecastDemand",
                "InventorySavings",
                "PotentialRevenueLoss",
                "InventoryRiskScore",
                "InventoryHealthScore",
                "StockCoverageDays",
                "WarehouseAllocationScore",
                "SupplierDelayRiskScore",
                "StockoutRiskScore",
                "OverstockRiskScore",
                "DemandSpikeRiskScore",
                "ExpectedProfitImprovement",
            ]
            if column in inventory_metrics.columns
        ]
        if metric_columns:
            base = base.merge(inventory_metrics[metric_columns].drop_duplicates(join_keys), on=join_keys, how="left")
        risk_columns = [
            column
            for column in [
                *join_keys,
                "InventoryRiskLevel",
                "InventoryRiskScore",
                "PotentialRevenueLoss",
                "StockoutRiskScore",
                "OverstockRiskScore",
                "SupplierDelayRiskScore",
            ]
            if column in inventory_risk.columns
        ]
        if risk_columns:
            base = base.merge(inventory_risk[risk_columns].drop_duplicates(join_keys), on=join_keys, how="left", suffixes=("", "_risk"))
    elif base.empty:
        base = inventory_metrics.copy()

    base = top_n(base, ["PotentialRevenueLoss", "InventoryRiskScore", "InventorySavings"], config.max_inventory_decisions)
    if base.empty:
        return _empty_decisions()

    recommendation = text_series(base, "Recommendation").str.lower()
    priority = text_series(base, "Priority")
    risk_score = coalesce_numeric(base, ["InventoryRiskScore", "InventoryRiskScore_risk"], 45.0)
    potential_loss = coalesce_numeric(base, ["PotentialRevenueLoss", "ForecastRevenue"], 0.0)
    savings = coalesce_numeric(base, ["InventorySavings"], 0.0)
    supplier_risk = coalesce_numeric(base, ["SupplierDelayRiskScore", "SupplierDelayRiskScore_risk"], 0.0)
    stockout_risk = coalesce_numeric(base, ["StockoutRiskScore", "StockoutRiskScore_risk"], 0.0)
    overstock_risk = coalesce_numeric(base, ["OverstockRiskScore", "OverstockRiskScore_risk"], 0.0)
    demand_spike_risk = coalesce_numeric(base, ["DemandSpikeRiskScore"], 0.0)

    decision_type = np.select(
        [
            recommendation.str.contains("supplier|delay", regex=True) | (supplier_risk >= 65),
            recommendation.str.contains("transfer|warehouse", regex=True),
            recommendation.str.contains("safety", regex=True),
            recommendation.str.contains("reduce|overstock|decrease", regex=True) | (overstock_risk >= 70),
            recommendation.str.contains("restock|reorder|increase", regex=True) | (stockout_risk >= 65),
        ],
        ["Supplier Escalation", "Warehouse Transfer", "Increase Safety Stock", "Reduce Overstock", "Restock SKU"],
        default="Increase Inventory",
    )

    priority_bonus = priority.str.upper().map({"P0": 100, "P1": 82, "P2": 60, "P3": 40}).fillna(55)
    out = pd.DataFrame(
        {
            "Domain": "Inventory",
            "DecisionType": decision_type,
            "EntityType": "Inventory series",
            "Entity": coalesce_text(base, ["SeriesKey", "Product"], "Inventory item"),
            "Product": coalesce_text(base, ["Product"], ""),
            "Country": coalesce_text(base, ["Country"], ""),
            "ProductCategory": coalesce_text(base, ["ProductCategory"], ""),
            "Warehouse": coalesce_text(base, ["Warehouse"], ""),
            "BusinessImpact": "High",
            "RevenueOpportunity": potential_loss * 0.55 + coalesce_numeric(base, ["ForecastRevenue"], 0.0) * 0.04,
            "CostReduction": np.where(decision_type == "Reduce Overstock", savings * 0.60 + potential_loss * 0.10, savings * 0.15),
            "InventorySavings": savings,
            "RetentionGain": 0.0,
            "ProfitImprovement": coalesce_numeric(base, ["ExpectedProfitImprovement"], 0.0) + potential_loss * 0.08,
            "ForecastRisk": demand_spike_risk,
            "InventoryRisk": risk_score,
            "CustomerRisk": 0.0,
            "RevenueRisk": normalize_score(potential_loss),
            "SupplierRisk": supplier_risk,
            "OperationalRisk": (risk_score * 0.60 + priority_bonus * 0.40).clip(0, 100),
            "UrgencyScore": (risk_score * 0.55 + priority_bonus * 0.45).clip(0, 100),
            "Reasoning": coalesce_text(
                base,
                ["BusinessExplanation", "Recommendation"],
                "Inventory optimization signals indicate action is required.",
            ),
            "SuggestedAction": coalesce_text(base, ["Recommendation"], "Execute inventory optimization recommendation."),
            "SourcePhase": "Phase 4 - Enterprise Inventory Optimization",
            "SourceArtifact": "inventory_recommendations.csv",
        }
    )

    transfer_candidates = pd.DataFrame()
    if "WarehouseAllocationScore" in inventory_metrics.columns:
        transfer_candidates = inventory_metrics[
            pd.to_numeric(inventory_metrics["WarehouseAllocationScore"], errors="coerce").fillna(100) <= 35
        ].head(20)
    if not transfer_candidates.empty:
        transfer_out = pd.DataFrame(
            {
                "Domain": "Inventory",
                "DecisionType": "Warehouse Transfer",
                "EntityType": "Warehouse allocation",
                "Entity": coalesce_text(transfer_candidates, ["SeriesKey", "Product"], "Warehouse allocation"),
                "Product": coalesce_text(transfer_candidates, ["Product"], ""),
                "Country": coalesce_text(transfer_candidates, ["Country"], ""),
                "ProductCategory": coalesce_text(transfer_candidates, ["ProductCategory"], ""),
                "Warehouse": coalesce_text(transfer_candidates, ["Warehouse"], ""),
                "BusinessImpact": "Medium",
                "RevenueOpportunity": coalesce_numeric(transfer_candidates, ["PotentialRevenueLoss"], 0.0) * 0.30,
                "CostReduction": coalesce_numeric(transfer_candidates, ["InventorySavings"], 0.0) * 0.25,
                "InventorySavings": coalesce_numeric(transfer_candidates, ["InventorySavings"], 0.0),
                "RetentionGain": 0.0,
                "ProfitImprovement": coalesce_numeric(transfer_candidates, ["ExpectedProfitImprovement"], 0.0),
                "ForecastRisk": coalesce_numeric(transfer_candidates, ["DemandSpikeRiskScore"], 0.0),
                "InventoryRisk": coalesce_numeric(transfer_candidates, ["InventoryRiskScore"], 50.0),
                "CustomerRisk": 0.0,
                "RevenueRisk": normalize_score(coalesce_numeric(transfer_candidates, ["PotentialRevenueLoss"], 0.0)),
                "SupplierRisk": coalesce_numeric(transfer_candidates, ["SupplierDelayRiskScore"], 0.0),
                "OperationalRisk": 72.0,
                "UrgencyScore": 68.0,
                "Reasoning": "Warehouse allocation score is low enough to justify transfer review.",
                "SuggestedAction": "Move available stock to the warehouse-market pair with the highest demand coverage gap.",
                "SourcePhase": "Phase 4 - Enterprise Inventory Optimization",
                "SourceArtifact": "inventory_metrics.csv",
            }
        )
        out = pd.concat([out, transfer_out], ignore_index=True)

    return _standardize(out)


def build_customer_decisions(
    customer_segments: pd.DataFrame,
    churn_predictions: pd.DataFrame,
    customer_actions: pd.DataFrame,
    config: DecisionConfig,
) -> pd.DataFrame:
    if customer_segments.empty and churn_predictions.empty:
        return _empty_decisions()

    churn = churn_predictions.copy()
    if not customer_actions.empty and "CustomerID" in churn.columns and "CustomerID" in customer_actions.columns:
        action_columns = [column for column in customer_actions.columns if column not in churn.columns or column == "CustomerID"]
        churn = churn.merge(customer_actions[action_columns], on="CustomerID", how="left")

    churn["ChurnProbability"] = numeric_series(churn, "ChurnProbability")
    churn["ExpectedLifetimeValue"] = coalesce_numeric(churn, ["ExpectedLifetimeValue", "PredictedCLV", "HistoricalCLV"], 0.0)
    high_risk = churn[
        (churn["ChurnProbability"] >= 0.35)
        | text_series(churn, "RiskCategory").isin(["Critical", "High"])
    ]
    high_risk = top_n(high_risk, ["ExpectedLifetimeValue", "ChurnProbability"], config.max_customer_decisions)

    retain_out = pd.DataFrame()
    if not high_risk.empty:
        churn_score = (high_risk["ChurnProbability"] * 100).clip(0, 100)
        value_score = normalize_score(high_risk["ExpectedLifetimeValue"])
        retain_out = pd.DataFrame(
            {
                "Domain": "Churn",
                "DecisionType": "Retain High Value Customer",
                "EntityType": "Customer",
                "Entity": text_series(high_risk, "CustomerID"),
                "Product": "",
                "Country": coalesce_text(high_risk, ["DominantCountry", "Country"], ""),
                "ProductCategory": "",
                "Warehouse": "",
                "BusinessImpact": "High",
                "RevenueOpportunity": 0.0,
                "CostReduction": 0.0,
                "InventorySavings": 0.0,
                "RetentionGain": high_risk["ExpectedLifetimeValue"] * high_risk["ChurnProbability"] * 0.42,
                "ProfitImprovement": high_risk["ExpectedLifetimeValue"] * 0.08,
                "ForecastRisk": 0.0,
                "InventoryRisk": 0.0,
                "CustomerRisk": churn_score,
                "RevenueRisk": value_score,
                "SupplierRisk": 0.0,
                "OperationalRisk": 35.0,
                "UrgencyScore": (churn_score * 0.65 + value_score * 0.35).clip(0, 100),
                "Reasoning": "Customer has elevated churn probability and meaningful lifetime value at risk.",
                "SuggestedAction": coalesce_text(high_risk, ["RecommendedAction"], "Launch personalized retention outreach."),
                "SourcePhase": "Phase 5 - Enterprise Customer Churn Intelligence",
                "SourceArtifact": "customer_churn_predictions.csv",
            }
        )

    segments = customer_segments.copy()
    segments["PredictedCLV"] = coalesce_numeric(segments, ["PredictedCLV", "HistoricalCLV", "Monetary"], 0.0)
    vip = segments[
        text_series(segments, "CustomerTier").str.contains("VIP|High", case=False, regex=True)
        | (segments["PredictedCLV"] >= segments["PredictedCLV"].quantile(0.80))
    ]
    vip = top_n(vip, ["PredictedCLV", "Revenue"], max(20, config.max_customer_decisions // 2))

    upsell_out = pd.DataFrame()
    if not vip.empty:
        clv_score = normalize_score(vip["PredictedCLV"])
        upsell_out = pd.DataFrame(
            {
                "Domain": "Customer",
                "DecisionType": "Upsell Premium Products",
                "EntityType": "Customer segment",
                "Entity": coalesce_text(vip, ["Segment", "CustomerID"], "High value customer"),
                "Product": "",
                "Country": "",
                "ProductCategory": "",
                "Warehouse": "",
                "BusinessImpact": "Medium",
                "RevenueOpportunity": vip["PredictedCLV"] * 0.08,
                "CostReduction": 0.0,
                "InventorySavings": 0.0,
                "RetentionGain": vip["PredictedCLV"] * 0.04,
                "ProfitImprovement": vip["PredictedCLV"] * 0.03,
                "ForecastRisk": 0.0,
                "InventoryRisk": 0.0,
                "CustomerRisk": 20.0,
                "RevenueRisk": clv_score * 0.40,
                "SupplierRisk": 0.0,
                "OperationalRisk": 30.0,
                "UrgencyScore": clv_score * 0.55 + 25.0,
                "Reasoning": "Customer intelligence identifies high predicted CLV and premium monetization potential.",
                "SuggestedAction": "Offer premium assortment, bundles, and loyalty-tier incentives.",
                "SourcePhase": "Phase 2 - Customer Intelligence",
                "SourceArtifact": "customer_segments.csv",
            }
        )

    return _standardize(pd.concat([retain_out, upsell_out], ignore_index=True))


def build_business_decisions(
    future_predictions: pd.DataFrame,
    forecast_comparison: pd.DataFrame,
    inventory_recommendations: pd.DataFrame,
    inventory_metrics: pd.DataFrame,
    inventory_risk: pd.DataFrame,
    customer_segments: pd.DataFrame,
    churn_predictions: pd.DataFrame,
    customer_actions: pd.DataFrame,
    config: DecisionConfig,
) -> pd.DataFrame:
    decisions = pd.concat(
        [
            build_forecast_decisions(future_predictions, forecast_comparison, config),
            build_inventory_decisions(inventory_recommendations, inventory_metrics, inventory_risk, config),
            build_customer_decisions(customer_segments, churn_predictions, customer_actions, config),
        ],
        ignore_index=True,
    )
    return _standardize(decisions)
