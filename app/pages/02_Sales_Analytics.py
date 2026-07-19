from __future__ import annotations

import pandas as pd
import streamlit as st

from components.cards import KpiCard, render_kpi_cards, render_section_header
from components.charts import bar_chart, line_chart, render_plotly, scatter_chart, treemap_chart
from components.filters import render_filter_bar
from components.sidebar import render_sidebar
from components.tables import render_dataframe
from components.utils import bootstrap_page, format_change, format_compact, format_currency, load_data_bundle


theme_mode = bootstrap_page("Sales Analytics", "💹")
data = load_data_bundle()
sales = data["sales"].copy()

render_sidebar(
    theme_mode=theme_mode,
    page_label="Sales Analytics",
    summary={
        "Revenue": format_currency(sales["Revenue"].sum()) if "Revenue" in sales.columns else "n/a",
        "Orders": format_compact(sales["InvoiceNo"].nunique()) if "InvoiceNo" in sales.columns else "n/a",
        "Products": format_compact(sales["Description"].nunique()) if "Description" in sales.columns else "n/a",
    },
)

st.markdown(
    """
<div class="rp-hero">
  <div class="rp-hero-title">Sales Analytics</div>
  <div class="rp-hero-subtitle">Track revenue growth, basket quality, product mix, and market performance.</div>
</div>
""",
    unsafe_allow_html=True,
)

with st.container(border=True):
    render_section_header("Sales Filters", "Narrow the story by date, geography, product category, and customer segment.")
    sales, selections = render_filter_bar(
        sales,
        date_column="InvoiceDate",
        categorical_columns=["Country", "ProductCategory"],
        key_prefix="sales",
    )

sales["InvoiceDate"] = pd.to_datetime(sales["InvoiceDate"], errors="coerce")
sales = sales.dropna(subset=["InvoiceDate"])
monthly = sales.groupby(pd.Grouper(key="InvoiceDate", freq="ME")).agg(Revenue=("Revenue", "sum"), Orders=("InvoiceNo", "nunique")).reset_index()
country = sales.groupby("Country", dropna=False).agg(Revenue=("Revenue", "sum"), Orders=("InvoiceNo", "nunique"), Profit=("Profit", "sum")).reset_index().sort_values("Revenue", ascending=False).head(12)
category = sales.groupby("ProductCategory", dropna=False).agg(Revenue=("Revenue", "sum"), Profit=("Profit", "sum"), AOV=("AverageOrderValue", "mean")).reset_index().sort_values("Revenue", ascending=False)
products = sales.groupby(["Description", "ProductCategory"], dropna=False).agg(Revenue=("Revenue", "sum"), Orders=("InvoiceNo", "nunique"), Profit=("Profit", "sum")).reset_index().sort_values("Revenue", ascending=False).head(15)

recent_month_revenue = float(monthly["Revenue"].iloc[-1]) if not monthly.empty else 0.0
previous_month_revenue = float(monthly["Revenue"].iloc[-2]) if len(monthly) > 1 else 0.0

render_kpi_cards(
    [
        KpiCard("Revenue", format_currency(sales["Revenue"].sum()), format_change(recent_month_revenue, previous_month_revenue, percent=True), "Filtered sales revenue", "positive", "💰"),
        KpiCard("Orders", format_compact(sales["InvoiceNo"].nunique()), "Unique invoice count", "Order volume", "neutral", "🧾"),
        KpiCard("Average Order Value", format_currency(sales["AverageOrderValue"].mean()) if "AverageOrderValue" in sales.columns else "n/a", "Average basket value in context", "Basket quality", "positive", "🛍️"),
        KpiCard("Gross Profit", format_currency(sales["Profit"].sum()), "Estimated profit from the transaction fact", "Margin signal", "neutral", "📊"),
    ],
    columns=4,
)

tabs = st.tabs(["Revenue Trend", "Product Mix", "Market View", "Detail Table"])
with tabs[0]:
    render_section_header("Monthly Revenue Trend", "Revenue and order pace across the selected context.")
    fig = line_chart(monthly, "InvoiceDate", "Revenue", title="Revenue Trend", mode=theme_mode, height=360, markers=True)
    render_plotly(fig)
with tabs[1]:
    col1, col2 = st.columns([1, 1], gap="large")
    with col1:
        render_section_header("Category Mix", "Revenue contribution by product category.")
        fig = treemap_chart(category, ["ProductCategory"], "Revenue", color="Profit", title="Category Contribution", mode=theme_mode, height=360)
        render_plotly(fig)
    with col2:
        render_section_header("Top Products", "The highest-revenue items in the current filter context.")
        fig = bar_chart(products, "Revenue", "Description", title="Top Products by Revenue", mode=theme_mode, height=360, orientation="h")
        render_plotly(fig)
with tabs[2]:
    col1, col2 = st.columns([1.15, 0.85], gap="large")
    with col1:
        render_section_header("Country Revenue", "Top markets ranked by sales and profit.")
        fig = bar_chart(country, "Country", "Revenue", title="Revenue by Country", mode=theme_mode, height=360)
        render_plotly(fig)
    with col2:
        render_section_header("Basket Quality", "AOV versus profit by category.")
        fig = scatter_chart(category, "Revenue", "AOV", size="Profit", color="ProductCategory", title="Category Revenue vs AOV", mode=theme_mode, height=360)
        render_plotly(fig)
with tabs[3]:
    render_section_header("Sales Detail", "A compact preview of the current sales facts.")
    preview_columns = [
        column
        for column in ["InvoiceNo", "InvoiceDate", "Country", "ProductCategory", "Description", "Revenue", "Profit", "AverageOrderValue"]
        if column in sales.columns
    ]
    preview = sales[preview_columns] if preview_columns else sales
    if "InvoiceDate" in preview.columns:
        preview = preview.sort_values("InvoiceDate", ascending=False)
    preview = preview.head(25)
    render_dataframe(preview, height=420)
