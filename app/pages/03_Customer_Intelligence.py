from __future__ import annotations

import pandas as pd
import streamlit as st

from components.cards import KpiCard, render_kpi_cards, render_section_header
from components.charts import bar_chart, donut_chart, render_plotly, scatter_chart, heatmap_chart
from components.filters import render_filter_bar
from components.sidebar import render_sidebar
from components.tables import render_dataframe
from components.utils import bootstrap_page, format_compact, format_currency, load_data_bundle


def _normalize_customer_id(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    if "CustomerID" in data.columns:
        data["CustomerID"] = pd.to_numeric(data["CustomerID"], errors="coerce").round().astype("Int64")
    return data


theme_mode = bootstrap_page("Customer Intelligence", "👥")
data = load_data_bundle()

rfm = _normalize_customer_id(data["rfm_table"])
segments = _normalize_customer_id(data["customer_segments"])
retention = _normalize_customer_id(data["customer_retention_metrics"])
health = _normalize_customer_id(data["customer_health_scores"])
probability = _normalize_customer_id(data["customer_probability_scores"])
actions = _normalize_customer_id(data["customer_business_actions"])
churn = _normalize_customer_id(data["customer_churn_predictions"])

customer = rfm.copy()
segment_columns = [column for column in ["CustomerID", "Cluster", "Segment", "ClusterSize"] if column in segments.columns]
if "CustomerID" in customer.columns and "CustomerID" in segment_columns:
    customer = customer.merge(
        segments[segment_columns],
        on="CustomerID",
        how="left",
        suffixes=("", "_segment"),
    )
if not health.empty:
    customer = customer.merge(health, on="CustomerID", how="left", suffixes=("", "_health"))
if not probability.empty:
    customer = customer.merge(probability, on="CustomerID", how="left", suffixes=("", "_probability"))
if not actions.empty:
    customer = customer.merge(actions, on="CustomerID", how="left", suffixes=("", "_action"))
if not churn.empty:
    churn_columns = [
        column
        for column in [
            "CustomerID",
            "ChurnProbability",
            "RetentionProbability",
            "ExpectedLifetimeValue",
            "RiskCategory",
            "HealthBand",
            "CustomerSegment",
            "RecommendedAction",
            "DominantCountry",
        ]
        if column in churn.columns
    ]
    customer = customer.merge(
        churn[churn_columns],
        on="CustomerID",
        how="left",
        suffixes=("", "_churn"),
    ) if "CustomerID" in churn_columns else customer

render_sidebar(
    theme_mode=theme_mode,
    page_label="Customer Intelligence",
    summary={
        "Customers": format_compact(customer["CustomerID"].nunique()) if "CustomerID" in customer.columns else "n/a",
        "CLV": format_currency(customer["PredictedCLV"].mean()) if "PredictedCLV" in customer.columns else "n/a",
        "Health": f"{float(customer['CustomerHealthScore'].mean()):.1f}" if "CustomerHealthScore" in customer.columns else "n/a",
    },
)

st.markdown(
    """
<div class="rp-hero">
  <div class="rp-hero-title">Customer Intelligence</div>
  <div class="rp-hero-subtitle">Profile customer value, RFM segments, health, and retention pressure in one workspace.</div>
</div>
""",
    unsafe_allow_html=True,
)

with st.container(border=True):
    render_section_header("Customer Filters", "Focus the analysis by tier, segment, health, risk, and geography.")
    customer, selections = render_filter_bar(
        customer,
        categorical_columns=["CustomerTier", "Segment", "HealthBand", "RiskCategory", "DominantCountry"],
        key_prefix="customer",
    )

render_kpi_cards(
    [
        KpiCard("Customers", format_compact(customer["CustomerID"].nunique()), "Unique customers in the segment view", "Customer base", "neutral", "👥"),
        KpiCard("Average CLV", format_currency(customer["PredictedCLV"].mean()) if "PredictedCLV" in customer.columns else "n/a", "Average predicted customer value", "Value concentration", "positive", "💎"),
        KpiCard("Health Score", f"{float(customer['CustomerHealthScore'].mean()):.1f}" if "CustomerHealthScore" in customer.columns else "n/a", "Average customer health score", "Resilience", "positive", "❤️"),
        KpiCard("VIP Customers", format_compact((customer["HealthBand"] == "VIP").sum()) if "HealthBand" in customer.columns else "n/a", "High-value customer count", "Priority service", "neutral", "⭐"),
        KpiCard("High Risk", format_compact(customer["RiskCategory"].isin(["Critical", "High"]).sum()) if "RiskCategory" in customer.columns else "n/a", "Customers needing attention", "Retention workload", "danger", "🛡️"),
        KpiCard("Revenue per Customer", format_currency(customer["Revenue"].mean()) if "Revenue" in customer.columns else "n/a", "Average revenue per customer", "Monetization", "neutral", "💵"),
    ],
    columns=3,
)

top = st.columns([1.1, 0.9], gap="large")
with top[0]:
    render_section_header("RFM Segments", "Recency, frequency, and monetary relationship by customer profile.")
    if customer.empty or not {"Recency", "Frequency", "Monetary"}.issubset(customer.columns):
        st.info("RFM data is not available.")
    else:
        fig = scatter_chart(
            customer,
            "Recency",
            "Frequency",
            size="Monetary" if "Monetary" in customer.columns else None,
            color="Segment" if "Segment" in customer.columns else None,
            hover_data=["CustomerID", "PredictedCLV", "CustomerHealthScore"] if "PredictedCLV" in customer.columns else ["CustomerID"],
            title="Recency vs Frequency",
            mode=theme_mode,
            height=360,
        )
        render_plotly(fig)
with top[1]:
    render_section_header("Segment Mix", "Revenue contribution from each customer segment.")
    if customer.empty or "Segment" not in customer.columns:
        st.info("Customer segment data is not available.")
    else:
        segment_mix = customer.groupby("Segment", dropna=False).agg(Customers=("CustomerID", "nunique"), Revenue=("Revenue", "sum")).reset_index().sort_values("Customers", ascending=False)
        fig = donut_chart(segment_mix, "Segment", "Customers", title="Customer Segment Share", mode=theme_mode, height=360)
        render_plotly(fig)

bottom_left, bottom_right = st.columns([1, 1], gap="large")
with bottom_left:
    render_section_header("Health Distribution", "Customer health and risk bands from the churn layer.")
    if customer.empty or "HealthBand" not in customer.columns:
        st.info("Health band data is not available.")
    else:
        health_mix = customer.groupby("HealthBand", dropna=False).agg(Customers=("CustomerID", "nunique")).reset_index().sort_values("Customers", ascending=False)
        fig = bar_chart(health_mix, "HealthBand", "Customers", title="Health Band Distribution", mode=theme_mode, height=330)
        render_plotly(fig)
with bottom_right:
    render_section_header("Risk Heatmap", "Segment and health overlap for the customer portfolio.")
    if customer.empty or not {"Segment", "HealthBand"}.issubset(customer.columns):
        st.info("Heatmap data is not available.")
    else:
        heat = pd.crosstab(customer["Segment"].fillna("Unknown"), customer["HealthBand"].fillna("Unknown"))
        fig = heatmap_chart(heat, title="Segment vs Health Band", mode=theme_mode, height=330)
        render_plotly(fig)

st.divider()
render_section_header("Top Customer Profiles", "The highest-value or highest-risk customer records in the active view.")
profile_columns = [column for column in ["CustomerID", "Segment", "CustomerTier", "PredictedCLV", "CustomerHealthScore", "RiskCategory", "RecommendedAction", "ChurnProbability"] if column in customer.columns]
top_profiles = customer[profile_columns] if profile_columns else customer.head(20)
if "PredictedCLV" in top_profiles.columns:
    top_profiles = top_profiles.sort_values("PredictedCLV", ascending=False)
elif "ChurnProbability" in top_profiles.columns:
    top_profiles = top_profiles.sort_values("ChurnProbability", ascending=False)
render_dataframe(top_profiles.head(25), height=360)
