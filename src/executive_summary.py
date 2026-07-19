from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from decision_utils import format_currency
from report_utils import frame_to_markdown_like


def build_executive_summary(
    decisions: pd.DataFrame,
    alerts: pd.DataFrame,
    scenarios: pd.DataFrame,
    risk_summary: pd.DataFrame,
    roi_summary: pd.DataFrame,
) -> pd.DataFrame:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    top_opportunity = decisions.sort_values("FinancialImpact", ascending=False).head(1)
    top_risk = decisions.sort_values("BusinessRiskScore", ascending=False).head(1)
    immediate = decisions[decisions["TimeSensitivity"].eq("Immediate")] if "TimeSensitivity" in decisions.columns else pd.DataFrame()
    best_scenario = scenarios.sort_values("ProfitImpact", ascending=False).head(1) if not scenarios.empty else pd.DataFrame()
    worst_scenario = scenarios.sort_values("RiskScore", ascending=False).head(1) if not scenarios.empty else pd.DataFrame()

    rows = [
        {
            "SummaryType": "Top Opportunities",
            "Title": _title(top_opportunity, "Highest financial impact recommendation"),
            "Value": _money(top_opportunity, "FinancialImpact"),
            "Narrative": _narrative(top_opportunity, "SuggestedAction"),
            "Priority": _value(top_opportunity, "PriorityBand", "n/a"),
            "Owner": "Executive Team",
            "Timeframe": _value(top_opportunity, "TimeSensitivity", "This Week"),
            "GeneratedAt": now,
        },
        {
            "SummaryType": "Top Risks",
            "Title": _title(top_risk, "Highest business risk"),
            "Value": _value(top_risk, "RiskLevel", "n/a"),
            "Narrative": _narrative(top_risk, "Reasoning"),
            "Priority": _value(top_risk, "PriorityBand", "n/a"),
            "Owner": "Risk Owner",
            "Timeframe": _value(top_risk, "TimeSensitivity", "Immediate"),
            "GeneratedAt": now,
        },
        {
            "SummaryType": "Critical Alerts",
            "Title": f"{len(alerts)} active business alerts",
            "Value": str(len(alerts[alerts.get("Severity", pd.Series(dtype=str)).isin(["Critical", "High"])])) if not alerts.empty else "0",
            "Narrative": "Critical and high alerts require weekly executive tracking until closed.",
            "Priority": "P0/P1",
            "Owner": "Operations",
            "Timeframe": "Immediate",
            "GeneratedAt": now,
        },
        {
            "SummaryType": "Business Wins",
            "Title": "Projected financial impact",
            "Value": format_currency(float(decisions.get("FinancialImpact", pd.Series(dtype=float)).sum())),
            "Narrative": "Decision engine combines revenue opportunity, inventory savings, cost reduction, retention gain, and profit improvement.",
            "Priority": "P1",
            "Owner": "Finance",
            "Timeframe": "This Month",
            "GeneratedAt": now,
        },
        {
            "SummaryType": "Revenue Drivers",
            "Title": "Revenue opportunity",
            "Value": format_currency(float(decisions.get("RevenueOpportunity", pd.Series(dtype=float)).sum())),
            "Narrative": "Primary drivers are demand capture, promotions, bundles, and premium upsell opportunities.",
            "Priority": "P1",
            "Owner": "Commercial",
            "Timeframe": "This Week",
            "GeneratedAt": now,
        },
        {
            "SummaryType": "Loss Drivers",
            "Title": "Scenario downside risk",
            "Value": _value(worst_scenario, "RiskLevel", "n/a"),
            "Narrative": _narrative(worst_scenario, "RecommendedResponse"),
            "Priority": "P1",
            "Owner": "Planning",
            "Timeframe": "This Week",
            "GeneratedAt": now,
        },
        {
            "SummaryType": "Immediate Actions",
            "Title": f"{len(immediate)} immediate actions",
            "Value": format_currency(float(immediate.get("FinancialImpact", pd.Series(dtype=float)).sum())) if not immediate.empty else "$0",
            "Narrative": "Immediate actions are the highest priority operating decisions for the next executive standup.",
            "Priority": "P0",
            "Owner": "Decision Office",
            "Timeframe": "Immediate",
            "GeneratedAt": now,
        },
        {
            "SummaryType": "Weekly Executive Summary",
            "Title": _value(best_scenario, "Scenario", "Decision intelligence ready"),
            "Value": _money(best_scenario, "ProfitImpact"),
            "Narrative": _narrative(best_scenario, "RecommendedResponse"),
            "Priority": "P1",
            "Owner": "Executive Team",
            "Timeframe": "Weekly",
            "GeneratedAt": now,
        },
    ]
    return pd.DataFrame(rows)


def render_executive_decision_report(
    decisions: pd.DataFrame,
    alerts: pd.DataFrame,
    summary: pd.DataFrame,
    scenarios: pd.DataFrame,
) -> str:
    return f"""# RetailPulse Executive Decision Report

Generated from the completed RetailPulse data engineering, customer intelligence, forecasting, inventory, churn, and Streamlit platform artifacts.

## Executive Summary

{frame_to_markdown_like(summary, rows=12)}

## Top Priority Decisions

{frame_to_markdown_like(decisions[["DecisionID", "PriorityBand", "PriorityScore", "DecisionType", "Domain", "Entity", "FinancialImpact", "ExpectedROI", "RiskLevel", "SuggestedAction"]].head(20), rows=20)}

## Critical Alerts

{frame_to_markdown_like(alerts.head(20), rows=20)}

## Scenario Outlook

{frame_to_markdown_like(scenarios[["Scenario", "RevenueImpact", "InventoryImpact", "ProfitImpact", "RiskLevel", "RecommendedResponse"]], rows=12)}
"""


def render_business_action_plan(priority_actions: pd.DataFrame) -> str:
    return f"""# RetailPulse Business Action Plan

## Immediate And Weekly Actions

{frame_to_markdown_like(priority_actions, rows=30)}

## Execution Guidance

- Assign an owner to each P0 and P1 decision.
- Track financial impact, risk movement, and completion status weekly.
- Use the scenario analysis output to stress test inventory and revenue commitments.
- Do not retrain models from this action plan; it consumes the already-generated artifacts.
"""


def render_strategic_recommendations(decisions: pd.DataFrame) -> str:
    strategic = (
        decisions.groupby(["Domain", "DecisionType"], dropna=False)
        .agg(
            Decisions=("DecisionID", "count"),
            FinancialImpact=("FinancialImpact", "sum"),
            AveragePriority=("PriorityScore", "mean"),
            AverageConfidence=("Confidence", "mean"),
        )
        .reset_index()
        .sort_values("FinancialImpact", ascending=False)
        if not decisions.empty
        else pd.DataFrame()
    )
    return f"""# RetailPulse Strategic Recommendations

## Recommendation Portfolio

{frame_to_markdown_like(strategic.round(2), rows=30)}

## Strategic Themes

- Protect high-revenue demand with coordinated inventory and supplier actions.
- Convert customer intelligence into retention and premium upsell motions.
- Use low-demand and overstock signals to reduce avoidable carrying cost.
- Treat recommendations as decision support over existing trained model outputs.
"""


def render_risk_assessment(risk_summary: pd.DataFrame, alerts: pd.DataFrame) -> str:
    return f"""# RetailPulse Risk Assessment

## Risk Summary

{frame_to_markdown_like(risk_summary, rows=12)}

## Alert Evidence

{frame_to_markdown_like(alerts[["AlertID", "AlertType", "Severity", "Domain", "Entity", "PriorityScore", "RiskLevel", "RecommendedAction"]].head(25), rows=25)}
"""


def render_roi_analysis(roi_summary: pd.DataFrame, decisions: pd.DataFrame) -> str:
    top_roi = decisions.sort_values("ExpectedROI", ascending=False).head(20) if not decisions.empty else pd.DataFrame()
    return f"""# RetailPulse ROI Analysis

## ROI By Domain

{frame_to_markdown_like(roi_summary, rows=12)}

## Top ROI Decisions

{frame_to_markdown_like(top_roi[["DecisionID", "DecisionType", "Domain", "Entity", "FinancialImpact", "ImplementationCost", "ExpectedROI"]], rows=20)}
"""


def _value(frame: pd.DataFrame, column: str, default: str) -> str:
    if frame.empty or column not in frame.columns:
        return default
    return str(frame.iloc[0][column])


def _money(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame.columns:
        return "$0"
    return format_currency(float(frame.iloc[0][column]))


def _title(frame: pd.DataFrame, default: str) -> str:
    if frame.empty:
        return default
    return f"{frame.iloc[0].get('DecisionType', default)} - {frame.iloc[0].get('Entity', '')}"


def _narrative(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame.columns:
        return "No narrative available."
    return str(frame.iloc[0][column])
