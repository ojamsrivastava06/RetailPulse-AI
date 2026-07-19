from __future__ import annotations

import pandas as pd
import streamlit as st

from components.cards import KpiCard, render_kpi_cards, render_section_header
from components.charts import bar_chart, donut_chart, line_chart, render_plotly, scatter_chart, waterfall_chart
from components.filters import render_filter_bar
from components.sidebar import render_sidebar
from components.tables import render_dataframe
from components.utils import bootstrap_page, format_change, format_compact, format_currency, load_data_bundle, safe_divide, calculate_forecast_accuracy, filter_forecast_comparison


def _summarize_forecast(data: pd.DataFrame, selections: dict[str, Any] | None = None) -> float:
    from typing import Any
    return calculate_forecast_accuracy(data, selections)


theme_mode = bootstrap_page("Executive Dashboard", "📈")
data = load_data_bundle()

sales = data["sales"].copy()
forecast_comparison = data["forecast_comparison"].copy()
inventory_dashboard = data["inventory_dashboard"].copy()
churn_predictions = data["customer_churn_predictions"].copy()
customer_health = data["customer_health_scores"].copy()
customer_segments = data["customer_segments"].copy()

render_sidebar(
    theme_mode=theme_mode,
    page_label="Executive Dashboard",
    summary={
        "Revenue": format_currency(sales["Revenue"].sum()) if "Revenue" in sales.columns else "n/a",
        "Forecast": f"{_summarize_forecast(forecast_comparison):.1%}" if not forecast_comparison.empty else "n/a",
        "Churn": f"{float(churn_predictions['ChurnProbability'].mean()):.1%}" if "ChurnProbability" in churn_predictions.columns else "n/a",
    },
)

st.markdown(
    """
<div class="rp-hero">
  <div class="rp-hero-title">Executive Dashboard</div>
  <div class="rp-hero-subtitle">A board-ready view of revenue, customer health, forecast quality, and inventory risk.</div>
</div>
""",
    unsafe_allow_html=True,
)

with st.container(border=True):
    render_section_header("Global Filters", "Use the executive controls to sync the story across the key metrics.")
    sales, selections = render_filter_bar(
        sales,
        date_column="InvoiceDate",
        categorical_columns=["Country", "ProductCategory"],
        key_prefix="executive",
    )

selected_countries = selections.get("Country", [])
selected_categories = selections.get("ProductCategory", [])
if selected_countries and "DominantCountry" in churn_predictions.columns:
    churn_predictions = churn_predictions[churn_predictions["DominantCountry"].astype(str).isin(selected_countries)]
if selected_countries:
    inventory_dashboard = inventory_dashboard[inventory_dashboard["Country"].astype(str).isin(selected_countries)] if "Country" in inventory_dashboard.columns else inventory_dashboard
if selected_categories and "ProductCategory" in customer_segments.columns:
    customer_segments = customer_segments[customer_segments["ProductCategory"].astype(str).isin(selected_categories)] if "ProductCategory" in customer_segments.columns else customer_segments
if selected_categories:
    inventory_dashboard = inventory_dashboard[inventory_dashboard["ProductCategory"].astype(str).isin(selected_categories)] if "ProductCategory" in inventory_dashboard.columns else inventory_dashboard

monthly_sales = (
    sales.assign(InvoiceDate=pd.to_datetime(sales["InvoiceDate"], errors="coerce"))
    .dropna(subset=["InvoiceDate"])
    .groupby(pd.Grouper(key="InvoiceDate", freq="ME"))
    .agg(Revenue=("Revenue", "sum"), Orders=("InvoiceNo", "nunique"))
    .reset_index()
)
country_sales = (
    sales.groupby("Country", dropna=False)
    .agg(Revenue=("Revenue", "sum"), Orders=("InvoiceNo", "nunique"), Profit=("Profit", "sum"))
    .reset_index()
    .sort_values("Revenue", ascending=False)
    .head(12)
)
segment_mix = (
    customer_segments.groupby("Segment", dropna=False)
    .agg(Customers=("CustomerID", "nunique"), Revenue=("Revenue", "sum"))
    .reset_index()
    .sort_values("Revenue", ascending=False)
    if not customer_segments.empty and "Segment" in customer_segments.columns
    else pd.DataFrame(columns=["Segment", "Customers", "Revenue"])
)
inventory_mix = (
    inventory_dashboard.groupby("Warehouse", dropna=False)
    .agg(InventoryCost=("TotalInventoryCost", "sum"), Savings=("InventorySavings", "sum"), Risk=("InventoryRiskScore", "mean"))
    .reset_index()
    .sort_values("InventoryCost", ascending=False)
    if not inventory_dashboard.empty and "Warehouse" in inventory_dashboard.columns
    else pd.DataFrame(columns=["Warehouse", "InventoryCost", "Savings", "Risk"])
)

executive_kpis = [
    KpiCard("Revenue", format_currency(sales["Revenue"].sum()), "Total revenue from the cleaned sales fact", "Core growth signal", "positive", "💰"),
    KpiCard("Orders", format_compact(sales["InvoiceNo"].nunique()), "Unique invoices in context", "Order count", "neutral", "🧾"),
    KpiCard("Customers", format_compact(sales["CustomerID"].nunique()), "Unique customers in context", "Customer base", "neutral", "👥"),
    KpiCard("Products", format_compact(sales["Description"].nunique()), "Unique products in context", "Assortment breadth", "neutral", "📦"),
    KpiCard("Global Forecast Accuracy", f"{_summarize_forecast(forecast_comparison, selections):.1%}", "Best Overall Forecast Model (evaluated on the complete forecasting dataset)", "Global metric (does not change with filters)", "positive", "🔮"),
    KpiCard("Inventory Health", f"{float(inventory_dashboard['InventoryHealthScore'].mean()):.1f}" if "InventoryHealthScore" in inventory_dashboard.columns else "n/a", "Average inventory health score", "Service risk", "warning", "📊"),
    KpiCard("Churn Rate", f"{float(churn_predictions['ChurnProbability'].mean()):.1%}" if "ChurnProbability" in churn_predictions.columns else "n/a", "Average churn probability", "Retention risk", "danger", "🛡️"),
    KpiCard("Customer Health", f"{float(customer_health['CustomerHealthScore'].mean()):.1f}" if "CustomerHealthScore" in customer_health.columns else "n/a", "Average customer health score", "Portfolio resilience", "positive", "❤️"),
]
render_kpi_cards(executive_kpis, columns=4)

left, right = st.columns([1.2, 0.8], gap="large")
with left:
    render_section_header("Revenue Trend", "Monthly revenue and order pace in the current filter context.")
    if monthly_sales.empty:
        st.info("Monthly sales trend is unavailable.")
    else:
        fig = line_chart(monthly_sales, "InvoiceDate", "Revenue", title="Revenue Trend", mode=theme_mode, height=360, markers=True)
        render_plotly(fig)
with right:
    render_section_header("Country Performance", "Top markets ranked by revenue and orders.")
    if country_sales.empty:
        st.info("Country performance is unavailable.")
    else:
        fig = bar_chart(country_sales, "Country", "Revenue", title="Revenue by Country", mode=theme_mode, height=360)
        render_plotly(fig)

bottom_left, bottom_right = st.columns([1, 1], gap="large")
with bottom_left:
    render_section_header("Customer Mix", "Segment contribution from the customer intelligence layer.")
    if segment_mix.empty:
        st.info("Segment mix is unavailable.")
    else:
        fig = donut_chart(segment_mix, "Segment", "Customers", title="Customer Segment Mix", mode=theme_mode, height=330)
        render_plotly(fig)
with bottom_right:
    render_section_header("Inventory by Warehouse", "Cost, savings, and risk from the inventory dashboard.")
    if inventory_mix.empty:
        st.info("Inventory warehouse mix is unavailable.")
    else:
        fig = scatter_chart(
            inventory_mix,
            "InventoryCost",
            "Risk",
            size="Savings" if "Savings" in inventory_mix.columns else None,
            color="Warehouse",
            hover_data=["Savings"] if "Savings" in inventory_mix.columns else None,
            title="Inventory Risk vs Cost",
            mode=theme_mode,
            height=330,
        )
        render_plotly(fig)

st.divider()
render_section_header("Action Summary", "Executive-level calls to action from the active filter context.")
action_table = pd.DataFrame(
    [
        {
            "Signal": "Sales",
            "Observation": f"Revenue is {format_change(monthly_sales['Revenue'].iloc[-1] if not monthly_sales.empty else 0, monthly_sales['Revenue'].iloc[-2] if len(monthly_sales) > 1 else 0, percent=True)}.",
        },
        {
            "Signal": "Forecast",
            "Observation": f"Best overall model accuracy is {_summarize_forecast(forecast_comparison, selections):.1%} (evaluated on the complete forecasting dataset).",
        },
        {
            "Signal": "Inventory",
            "Observation": f"Average inventory health is {float(inventory_dashboard['InventoryHealthScore'].mean()):.1f}." if "InventoryHealthScore" in inventory_dashboard.columns else "Inventory health metrics are unavailable.",
        },
        {
            "Signal": "Customer",
            "Observation": f"Average customer health is {float(customer_health['CustomerHealthScore'].mean()):.1f}." if "CustomerHealthScore" in customer_health.columns else "Customer health metrics are unavailable.",
        },
        {
            "Signal": "Churn",
            "Observation": f"Average churn probability is {float(churn_predictions['ChurnProbability'].mean()):.1%}." if "ChurnProbability" in churn_predictions.columns else "Churn metrics are unavailable.",
        },
    ]
)
render_dataframe(action_table, height=240)
