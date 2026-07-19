from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

from business_rules import build_business_decisions
from config import FINAL_PROCESSED_DATA_PATH, FIGURES_DIR, PROCESSED_OUTPUT_DIR
from decision_models import DecisionConfig, DecisionOutputPaths, DecisionRunResult
from decision_utils import read_csv
from executive_summary import (
    build_executive_summary,
    render_business_action_plan,
    render_executive_decision_report,
    render_risk_assessment,
    render_roi_analysis,
    render_strategic_recommendations,
)
from impact_analysis import build_roi_summary
from io_utils import save_figure, write_dataframe, write_text
from logger import get_logger
from recommendation_engine import build_business_alerts, build_priority_actions, score_recommendations
from risk_engine import build_risk_summary
from scenario_engine import build_scenario_analysis

logger = get_logger(__name__)


def load_decision_sources() -> dict[str, pd.DataFrame]:
    return {
        "sales": read_csv(FINAL_PROCESSED_DATA_PATH, parse_dates=("InvoiceDate",)),
        "future_predictions": read_csv(PROCESSED_OUTPUT_DIR / "future_predictions.csv", parse_dates=("Date",)),
        "forecast_comparison": read_csv(PROCESSED_OUTPUT_DIR / "forecast_comparison.csv"),
        "inventory_recommendations": read_csv(PROCESSED_OUTPUT_DIR / "inventory_recommendations.csv"),
        "inventory_metrics": read_csv(PROCESSED_OUTPUT_DIR / "inventory_metrics.csv"),
        "inventory_risk": read_csv(PROCESSED_OUTPUT_DIR / "inventory_risk.csv"),
        "inventory_dashboard": read_csv(PROCESSED_OUTPUT_DIR / "inventory_dashboard.csv"),
        "customer_segments": read_csv(PROCESSED_OUTPUT_DIR / "customer_segments.csv"),
        "churn_predictions": read_csv(PROCESSED_OUTPUT_DIR / "customer_churn_predictions.csv"),
        "customer_actions": read_csv(PROCESSED_OUTPUT_DIR / "customer_business_actions.csv"),
        "customer_leaderboard": read_csv(PROCESSED_OUTPUT_DIR / "customer_model_leaderboard.csv"),
    }


def run_decision_engine(
    *,
    config: DecisionConfig | None = None,
    paths: DecisionOutputPaths | None = None,
) -> DecisionRunResult:
    config = config or DecisionConfig()
    paths = paths or DecisionOutputPaths()
    sources = load_decision_sources()

    logger.info("Generating RetailPulse decision intelligence artifacts")
    raw_decisions = build_business_decisions(
        future_predictions=sources["future_predictions"],
        forecast_comparison=sources["forecast_comparison"],
        inventory_recommendations=sources["inventory_recommendations"],
        inventory_metrics=sources["inventory_metrics"],
        inventory_risk=sources["inventory_risk"],
        customer_segments=sources["customer_segments"],
        churn_predictions=sources["churn_predictions"],
        customer_actions=sources["customer_actions"],
        config=config,
    )
    scored_decisions = score_recommendations(
        raw_decisions,
        forecast_comparison=sources["forecast_comparison"],
        customer_leaderboard=sources["customer_leaderboard"],
        inventory_dashboard=sources["inventory_dashboard"],
        config=config,
    )

    scenarios = build_scenario_analysis(
        sources["future_predictions"],
        sources["inventory_dashboard"],
        sources["churn_predictions"],
        config,
    )
    alerts = build_business_alerts(scored_decisions)
    priority_actions = build_priority_actions(scored_decisions)
    risk_summary = build_risk_summary(scored_decisions, sources["inventory_dashboard"], sources["churn_predictions"])
    roi_summary = build_roi_summary(scored_decisions)
    executive_summary = build_executive_summary(scored_decisions, alerts, scenarios, risk_summary, roi_summary)
    recommendation_scores = _recommendation_scores(scored_decisions)

    csv_outputs = {
        "business_decisions": write_dataframe(scored_decisions, paths.business_decisions),
        "executive_summary": write_dataframe(executive_summary, paths.executive_summary),
        "business_alerts": write_dataframe(alerts, paths.business_alerts),
        "priority_actions": write_dataframe(priority_actions, paths.priority_actions),
        "risk_summary": write_dataframe(risk_summary, paths.risk_summary),
        "scenario_analysis": write_dataframe(scenarios, paths.scenario_analysis),
        "recommendation_scores": write_dataframe(recommendation_scores, paths.recommendation_scores),
    }

    reports = {
        "executive_decision_report": write_text(
            render_executive_decision_report(scored_decisions, alerts, executive_summary, scenarios),
            paths.executive_decision_report,
        ),
        "business_action_plan": write_text(render_business_action_plan(priority_actions), paths.business_action_plan),
        "strategic_recommendations": write_text(render_strategic_recommendations(scored_decisions), paths.strategic_recommendations),
        "risk_assessment": write_text(render_risk_assessment(risk_summary, alerts), paths.risk_assessment),
        "roi_analysis": write_text(render_roi_analysis(roi_summary, scored_decisions), paths.roi_analysis),
    }

    _save_decision_figures(scored_decisions, scenarios, risk_summary)
    logger.info("Decision intelligence generated: %s decisions, %s alerts", len(scored_decisions), len(alerts))
    return DecisionRunResult(
        decisions=len(scored_decisions),
        alerts=len(alerts),
        scenarios=len(scenarios),
        reports=reports,
        csv_outputs=csv_outputs,
    )


def _recommendation_scores(decisions: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "DecisionID",
        "Domain",
        "DecisionType",
        "Entity",
        "PriorityScore",
        "ImpactScore",
        "BusinessRiskScore",
        "Confidence",
        "ModelConfidence",
        "BusinessConfidence",
        "HistoricalAccuracy",
        "RecommendationReliability",
        "ExpectedROI",
        "FinancialImpact",
        "TimeSensitivity",
    ]
    return decisions[[column for column in columns if column in decisions.columns]].copy()


def _save_decision_figures(decisions: pd.DataFrame, scenarios: pd.DataFrame, risk_summary: pd.DataFrame) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    if not decisions.empty:
        fig, ax = plt.subplots(figsize=(9, 5))
        ax.scatter(decisions["BusinessRiskScore"], decisions["FinancialImpact"], s=decisions["PriorityScore"] * 2, alpha=0.65)
        ax.set_title("Decision Priority Matrix")
        ax.set_xlabel("Business Risk Score")
        ax.set_ylabel("Financial Impact")
        save_figure(fig, FIGURES_DIR / "decision_priority_matrix.png", dpi=180)

        domain_impact = decisions.groupby("Domain", dropna=False)["FinancialImpact"].sum().sort_values()
        fig, ax = plt.subplots(figsize=(8, 4.5))
        domain_impact.plot(kind="barh", ax=ax, color="#5B8DEF")
        ax.set_title("Financial Impact by Domain")
        ax.set_xlabel("Financial Impact")
        save_figure(fig, FIGURES_DIR / "decision_financial_impact_by_domain.png", dpi=180)

    if not scenarios.empty:
        fig, ax = plt.subplots(figsize=(9, 4.5))
        scenarios.sort_values("ProfitImpact").plot(kind="barh", x="Scenario", y="ProfitImpact", ax=ax, color="#2DD4BF", legend=False)
        ax.set_title("Scenario Profit Impact")
        ax.set_xlabel("Profit Impact")
        save_figure(fig, FIGURES_DIR / "decision_scenario_profit_impact.png", dpi=180)

    if not risk_summary.empty:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        risk_summary.sort_values("RiskScore").plot(kind="barh", x="RiskDomain", y="RiskScore", ax=ax, color="#F2B84B", legend=False)
        ax.set_title("Decision Risk Summary")
        ax.set_xlabel("Risk Score")
        save_figure(fig, FIGURES_DIR / "decision_risk_summary.png", dpi=180)


def main() -> dict[str, Any]:
    result = run_decision_engine()
    return {
        "decisions": result.decisions,
        "alerts": result.alerts,
        "scenarios": result.scenarios,
        "csv_outputs": {name: str(path) for name, path in result.csv_outputs.items()},
        "reports": {name: str(path) for name, path in result.reports.items()},
    }


if __name__ == "__main__":
    print(main())
