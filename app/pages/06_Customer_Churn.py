from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from components.cards import KpiCard, render_kpi_cards, render_section_header
from components.charts import bar_chart, donut_chart, render_plotly, scatter_chart
from components.filters import render_filter_bar
from components.sidebar import render_sidebar
from components.tables import render_dataframe
from components.utils import bootstrap_page, format_compact, format_currency, load_data_bundle, file_bytes


def _normalize_customer_id(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    if "CustomerID" in data.columns:
        data["CustomerID"] = pd.to_numeric(data["CustomerID"], errors="coerce").round().astype("Int64")
    return data


theme_mode = bootstrap_page("Customer Churn", "🛡️")
data = load_data_bundle()

churn = _normalize_customer_id(data["customer_churn_predictions"])
health = _normalize_customer_id(data["customer_health_scores"])
probability = _normalize_customer_id(data["customer_probability_scores"])
actions = _normalize_customer_id(data["customer_business_actions"])

churn_view = churn.copy()
if not health.empty and {"CustomerID"}.issubset(health.columns) and "CustomerID" in churn_view.columns:
    churn_view = churn_view.merge(health, on="CustomerID", how="left", suffixes=("", "_health"))
if not probability.empty and {"CustomerID"}.issubset(probability.columns) and "CustomerID" in churn_view.columns:
    churn_view = churn_view.merge(probability, on="CustomerID", how="left", suffixes=("", "_prob"))
if not actions.empty and {"CustomerID"}.issubset(actions.columns) and "CustomerID" in churn_view.columns:
    churn_view = churn_view.merge(actions, on="CustomerID", how="left", suffixes=("", "_action"))

render_sidebar(
    theme_mode=theme_mode,
    page_label="Customer Churn",
    summary={
        "Churn": f"{float(churn_view['ChurnProbability'].mean()):.1%}" if "ChurnProbability" in churn_view.columns else "n/a",
        "Health": f"{float(churn_view['CustomerHealthScore'].mean()):.1f}" if "CustomerHealthScore" in churn_view.columns else "n/a",
        "Actions": format_compact(churn_view["RecommendedAction"].nunique()) if "RecommendedAction" in churn_view.columns else "n/a",
    },
)

st.markdown(
    """
<div class="rp-hero">
  <div class="rp-hero-title">Customer Churn</div>
  <div class="rp-hero-subtitle">Prioritize retention actions using churn probability, health score, risk, and recommended action.</div>
</div>
""",
    unsafe_allow_html=True,
)

with st.container(border=True):
    render_section_header("Churn Filters", "Use risk, health, segment, and country to isolate the customers that matter most.")
    churn_view, selections = render_filter_bar(
        churn_view,
        categorical_columns=["RiskCategory", "HealthBand", "CustomerSegment", "DominantCountry", "RecommendedAction"],
        key_prefix="churn",
    )

render_kpi_cards(
    [
        KpiCard("Churn Rate", f"{float(churn_view['ChurnProbability'].mean()):.1%}" if "ChurnProbability" in churn_view.columns else "n/a", "Average churn probability in the selected view", "Retention urgency", "danger", "🛡️"),
        KpiCard("Retention Rate", f"{(1 - float(churn_view['ChurnProbability'].mean())):.1%}" if "ChurnProbability" in churn_view.columns else "n/a", "Retention complement of churn", "Loyalty signal", "positive", "✅"),
        KpiCard("High Risk Customers", format_compact(churn_view[churn_view["RiskCategory"].isin(["Critical", "High"])].shape[0]) if "RiskCategory" in churn_view.columns else "n/a", "Customers requiring intervention", "Workload", "warning", "⚠️"),
        KpiCard("Average Health", f"{float(churn_view['CustomerHealthScore'].mean()):.1f}" if "CustomerHealthScore" in churn_view.columns else "n/a", "Average customer health score", "Portfolio health", "positive", "❤️"),
        KpiCard("Customer LTV", format_currency(churn_view["ExpectedLifetimeValue"].sum()) if "ExpectedLifetimeValue" in churn_view.columns else "n/a", "Portfolio lifetime value", "Value at stake", "neutral", "💎"),
        KpiCard("Actions", format_compact(churn_view["RecommendedAction"].nunique()) if "RecommendedAction" in churn_view.columns else "n/a", "Unique recommendation types", "Action mix", "neutral", "🧭"),
    ],
    columns=3,
)

top = st.columns([1.0, 1.0], gap="large")
with top[0]:
    render_section_header("Risk Distribution", "Where churn risk sits across the portfolio.")
    if churn_view.empty or "RiskCategory" not in churn_view.columns:
        st.info("Risk distribution is unavailable.")
    else:
        risk_mix = churn_view.groupby("RiskCategory", dropna=False).agg(Customers=("CustomerID", "nunique")).reset_index().sort_values("Customers", ascending=False)
        fig = donut_chart(risk_mix, "RiskCategory", "Customers", title="Risk Category Share", mode=theme_mode, height=360)
        render_plotly(fig)
with top[1]:
    render_section_header("Health Bands", "Customer health distribution across the selected view.")
    if churn_view.empty or "HealthBand" not in churn_view.columns:
        st.info("Health band data is unavailable.")
    else:
        health_mix = churn_view.groupby("HealthBand", dropna=False).agg(Customers=("CustomerID", "nunique")).reset_index().sort_values("Customers", ascending=False)
        fig = bar_chart(health_mix, "HealthBand", "Customers", title="Health Band Distribution", mode=theme_mode, height=360)
        render_plotly(fig)

middle_left, middle_right = st.columns([1.15, 0.85], gap="large")
with middle_left:
    render_section_header("Churn vs Value", "Probability against lifetime value to highlight the save-now list.")
    if churn_view.empty or not {"ChurnProbability", "ExpectedLifetimeValue"}.issubset(churn_view.columns):
        st.info("Churn value scatter is unavailable.")
    else:
        fig = scatter_chart(
            churn_view,
            "ChurnProbability",
            "ExpectedLifetimeValue",
            size="CustomerHealthScore" if "CustomerHealthScore" in churn_view.columns else None,
            color="RiskCategory" if "RiskCategory" in churn_view.columns else None,
            hover_data=["CustomerID", "CustomerSegment", "RecommendedAction"] if "CustomerSegment" in churn_view.columns else ["CustomerID"],
            title="Churn Probability vs Lifetime Value",
            mode=theme_mode,
            height=340,
        )
        render_plotly(fig)
with middle_right:
    render_section_header("Action Mix", "Recommended actions by customer count.")
    if churn_view.empty or "RecommendedAction" not in churn_view.columns:
        st.info("Action distribution is unavailable.")
    else:
        action_mix = churn_view.groupby("RecommendedAction", dropna=False).agg(Customers=("CustomerID", "nunique")).reset_index().sort_values("Customers", ascending=False).head(10)
        fig = bar_chart(action_mix, "RecommendedAction", "Customers", title="Recommended Actions", mode=theme_mode, height=340)
        render_plotly(fig)

st.divider()
figure_tabs = st.tabs(["SHAP / Drivers", "Top Customers", "Action Detail"])
with figure_tabs[0]:
    render_section_header("Driver Visuals", "Use the generated SHAP summary or risk matrix if it exists.")
    shap_path = Path(__file__).resolve().parents[2] / "reports" / "figures" / "33_shap_summary.png"
    if shap_path.exists():
        st.image(file_bytes(shap_path))
    else:
        st.info("No SHAP summary figure was found in the generated figures directory.")
with figure_tabs[1]:
    render_section_header("Top Customer Records", "The riskiest or highest-value customers in the current view.")
    detail_cols = [column for column in ["CustomerID", "ChurnProbability", "RetentionProbability", "CustomerHealthScore", "ExpectedLifetimeValue", "RiskCategory", "HealthBand", "RecommendedAction"] if column in churn_view.columns]
    detail_view = churn_view[detail_cols] if detail_cols else churn_view
    if "ChurnProbability" in detail_view.columns:
        detail_view = detail_view.sort_values("ChurnProbability", ascending=False)
    elif "ExpectedLifetimeValue" in detail_view.columns:
        detail_view = detail_view.sort_values("ExpectedLifetimeValue", ascending=False)
    render_dataframe(detail_view.head(25), height=320)
with figure_tabs[2]:
    render_section_header("Action Detail", "The text rationale behind the recommended action.")
    action_cols = [column for column in ["CustomerID", "RecommendedAction", "ActionReasoning", "ProbabilityConfidence", "RiskScore"] if column in churn_view.columns]
    render_dataframe(churn_view[action_cols].head(25), height=320)
