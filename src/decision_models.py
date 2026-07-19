from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from config import PROCESSED_OUTPUT_DIR, REPORTS_DIR


@dataclass(frozen=True)
class DecisionConfig:
    """Scoring and output controls for the decision intelligence layer."""

    max_forecast_decisions: int = 60
    max_inventory_decisions: int = 90
    max_customer_decisions: int = 80
    priority_weights: Mapping[str, float] = field(
        default_factory=lambda: {
            "financial": 0.34,
            "risk": 0.24,
            "confidence": 0.22,
            "urgency": 0.20,
        }
    )
    scenario_definitions: Mapping[str, Mapping[str, float]] = field(
        default_factory=lambda: {
            "Demand +10%": {"demand": 0.10, "price": 0.00, "supplier": 0.00, "churn": 0.00},
            "Demand +20%": {"demand": 0.20, "price": 0.00, "supplier": 0.00, "churn": 0.00},
            "Demand -20%": {"demand": -0.20, "price": 0.00, "supplier": 0.00, "churn": 0.00},
            "Holiday Season": {"demand": 0.28, "price": 0.02, "supplier": 0.06, "churn": -0.02},
            "Supplier Delay": {"demand": -0.04, "price": 0.00, "supplier": 0.22, "churn": 0.00},
            "Inventory Shortage": {"demand": -0.10, "price": 0.00, "supplier": 0.08, "churn": 0.02},
            "Customer Churn Increase": {"demand": -0.05, "price": 0.00, "supplier": 0.00, "churn": 0.12},
            "Price Increase": {"demand": -0.08, "price": 0.10, "supplier": 0.00, "churn": 0.03},
            "Price Discount": {"demand": 0.14, "price": -0.08, "supplier": 0.00, "churn": -0.02},
        }
    )


@dataclass(frozen=True)
class DecisionOutputPaths:
    """Canonical output locations for decision intelligence artifacts."""

    business_decisions: Path = PROCESSED_OUTPUT_DIR / "business_decisions.csv"
    executive_summary: Path = PROCESSED_OUTPUT_DIR / "executive_summary.csv"
    business_alerts: Path = PROCESSED_OUTPUT_DIR / "business_alerts.csv"
    priority_actions: Path = PROCESSED_OUTPUT_DIR / "priority_actions.csv"
    risk_summary: Path = PROCESSED_OUTPUT_DIR / "risk_summary.csv"
    scenario_analysis: Path = PROCESSED_OUTPUT_DIR / "scenario_analysis.csv"
    recommendation_scores: Path = PROCESSED_OUTPUT_DIR / "recommendation_scores.csv"

    executive_decision_report: Path = REPORTS_DIR / "executive_decision_report.md"
    business_action_plan: Path = REPORTS_DIR / "business_action_plan.md"
    strategic_recommendations: Path = REPORTS_DIR / "strategic_recommendations.md"
    risk_assessment: Path = REPORTS_DIR / "risk_assessment.md"
    roi_analysis: Path = REPORTS_DIR / "roi_analysis.md"


@dataclass(frozen=True)
class DecisionRunResult:
    decisions: int
    alerts: int
    scenarios: int
    reports: Mapping[str, Path]
    csv_outputs: Mapping[str, Path]
