from __future__ import annotations

import pandas as pd
import streamlit as st

from components.cards import KpiCard, render_kpi_cards, render_section_header
from components.charts import bar_chart, donut_chart, heatmap_chart, render_plotly, scatter_chart, treemap_chart
from components.filters import render_filter_bar
from components.sidebar import render_sidebar
from components.tables import render_dataframe
from components.utils import bootstrap_page, format_compact, format_currency, load_data_bundle


def _normalize_inventory(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    if "Date" in data.columns:
        data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    return data


theme_mode = bootstrap_page("Inventory Optimization", "📦")
data = load_data_bundle()

inventory = _normalize_inventory(data["inventory_dataset"])
inventory_dashboard = data["inventory_dashboard"]
inventory_metrics = data["inventory_metrics"]
inventory_risk = data["inventory_risk"]
inventory_recommendations = data["inventory_recommendations"]
abc_analysis = data["abc_analysis"]
xyz_analysis = data["xyz_analysis"]
abc_xyz_matrix = data["abc_xyz_matrix"]

render_sidebar(
    theme_mode=theme_mode,
    page_label="Inventory Optimization",
    summary={
        "Cost": format_currency(inventory["TotalInventoryCost"].sum()) if "TotalInventoryCost" in inventory.columns else "n/a",
        "Savings": format_currency(inventory["InventorySavings"].sum()) if "InventorySavings" in inventory.columns else "n/a",
        "Risk": f"{float(inventory['InventoryRiskScore'].mean()):.1f}" if "InventoryRiskScore" in inventory.columns else "n/a",
    },
)

st.markdown(
    """
<div class="rp-hero">
  <div class="rp-hero-title">Inventory Optimization</div>
  <div class="rp-hero-subtitle">Balance stock coverage, cost, EOQ, and replenishment priorities across the network.</div>
</div>
""",
    unsafe_allow_html=True,
)

with st.container(border=True):
    render_section_header("Inventory Filters", "Constrain the optimization view by warehouse, geography, category, and risk level.")
    inventory, selections = render_filter_bar(
        inventory,
        date_column="Date",
        categorical_columns=["Warehouse", "Country", "ProductCategory", "InventoryRiskLevel"],
        key_prefix="inventory",
    )

render_kpi_cards(
    [
        KpiCard("Inventory Cost", format_currency(inventory["TotalInventoryCost"].sum()) if "TotalInventoryCost" in inventory.columns else "n/a", "Carrying plus stockout cost", "Cost-to-serve", "neutral", "💸"),
        KpiCard("Inventory Savings", format_currency(inventory["InventorySavings"].sum()) if "InventorySavings" in inventory.columns else "n/a", "Optimization upside", "Value unlocked", "positive", "💚"),
        KpiCard("Safety Stock", f"{float(inventory['SafetyStock'].mean()):.0f}" if "SafetyStock" in inventory.columns else "n/a", "Average safety buffer", "Risk cushion", "neutral", "🧯"),
        KpiCard("Stock Coverage", f"{float(inventory['StockCoverageDays'].mean()):.1f}" if "StockCoverageDays" in inventory.columns else "n/a", "Average days of cover", "Availability", "neutral", "⏱️"),
        KpiCard("EOQ", f"{float(inventory['EconomicOrderQuantity'].mean()):.0f}" if "EconomicOrderQuantity" in inventory.columns else "n/a", "Economic order quantity", "Ordering efficiency", "neutral", "📐"),
        KpiCard("Risk Score", f"{float(inventory['InventoryRiskScore'].mean()):.1f}" if "InventoryRiskScore" in inventory.columns else "n/a", "Average inventory risk score", "Operational risk", "danger", "🛡️"),
    ],
    columns=3,
)

top = st.columns([1.0, 1.0], gap="large")
with top[0]:
    render_section_header("ABC Classification", "Value concentration by ABC class.")
    if abc_analysis.empty or "ABCClass" not in abc_analysis.columns:
        st.info("ABC analysis data is unavailable.")
    else:
        abc = abc_analysis.groupby("ABCClass", dropna=False).agg(Revenue=("TotalRevenue", "sum")).reset_index().sort_values("Revenue", ascending=False)
        fig = donut_chart(abc, "ABCClass", "Revenue", title="ABC Revenue Share", mode=theme_mode, height=360)
        render_plotly(fig)
with top[1]:
    render_section_header("XYZ Classification", "Demand variability by XYZ class.")
    if xyz_analysis.empty or "XYZClass" not in xyz_analysis.columns:
        st.info("XYZ analysis data is unavailable.")
    else:
        xyz = xyz_analysis.groupby("XYZClass", dropna=False).agg(SeriesCount=("SeriesKey", "nunique")).reset_index().sort_values("SeriesCount", ascending=False)
        fig = bar_chart(xyz, "XYZClass", "SeriesCount", title="XYZ Class Count", mode=theme_mode, height=360)
        render_plotly(fig)

middle_left, middle_right = st.columns([1.05, 0.95], gap="large")
with middle_left:
    render_section_header("Risk Heatmap", "Warehouse and product category risk distribution.")
    if inventory.empty or not {"Warehouse", "ProductCategory", "InventoryRiskLevel"}.issubset(inventory.columns):
        st.info("Risk heatmap is unavailable.")
    else:
        heat = pd.crosstab(inventory["Warehouse"].fillna("Unknown"), inventory["InventoryRiskLevel"].fillna("Unknown"))
        fig = heatmap_chart(heat, title="Warehouse by Risk Level", mode=theme_mode, height=340)
        render_plotly(fig)
with middle_right:
    render_section_header("Replenishment Scatter", "Safety stock, reorder point, and risk score.")
    if inventory.empty or not {"SafetyStock", "ReorderPoint", "InventoryRiskScore"}.issubset(inventory.columns):
        st.info("Replenishment scatter is unavailable.")
    else:
        fig = scatter_chart(
            inventory,
            "SafetyStock",
            "ReorderPoint",
            size="InventoryRiskScore",
            color="InventoryRiskLevel" if "InventoryRiskLevel" in inventory.columns else None,
            hover_data=["Warehouse", "ProductCategory", "SuggestedQuantity"] if "SuggestedQuantity" in inventory.columns else ["Warehouse", "ProductCategory"],
            title="Safety Stock vs Reorder Point",
            mode=theme_mode,
            height=340,
        )
        render_plotly(fig)

st.divider()
bottom_tabs = st.tabs(["Recommendations", "Metrics", "Risk"])
with bottom_tabs[0]:
    render_section_header("Inventory Recommendations", "Actionable replenishment guidance from the optimization engine.")
    recommendation_cols = [column for column in ["Product", "Country", "Warehouse", "ProductCategory", "HorizonDays", "Priority", "Recommendation", "SuggestedQuantity"] if column in inventory_recommendations.columns]
    render_dataframe(inventory_recommendations[recommendation_cols].head(25), height=280)
with bottom_tabs[1]:
    render_section_header("Inventory Metrics", "Classification and optimization metrics from the output tables.")
    render_dataframe(inventory_metrics.head(25), height=280)
with bottom_tabs[2]:
    render_section_header("Inventory Risk Snapshot", "A concise inventory risk table from the risk output.")
    render_dataframe(inventory_risk.head(25), height=280)

