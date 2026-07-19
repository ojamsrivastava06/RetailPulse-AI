from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from components.cards import KpiCard, NavigationCard, render_kpi_cards, render_navigation_cards, render_section_header
from components.charts import bar_chart, line_chart, render_plotly
from components.sidebar import render_sidebar
from components.tables import render_artifact_grid
from components.utils import (
    bootstrap_page,
    current_theme_mode,
    format_change,
    format_compact,
    format_currency,
    load_data_bundle,
    list_figures,
    list_models,
    list_reports,
    safe_divide,
    time_ago,
    calculate_forecast_accuracy,
)


def _month_series(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty or "InvoiceDate" not in frame.columns:
        return pd.DataFrame(columns=["InvoiceDate", "Revenue"])
    data = frame.copy()
    data["InvoiceDate"] = pd.to_datetime(data["InvoiceDate"], errors="coerce")
    monthly = (
        data.dropna(subset=["InvoiceDate"])
        .groupby(pd.Grouper(key="InvoiceDate", freq="ME"), dropna=True)
        .agg(Revenue=("Revenue", "sum"), Orders=("InvoiceNo", "nunique"))
        .reset_index()
    )
    return monthly


def _compare_recent_periods(frame: pd.DataFrame) -> tuple[float, float]:
    if frame.empty or "InvoiceDate" not in frame.columns:
        return 0.0, 0.0
    data = frame.copy()
    data["InvoiceDate"] = pd.to_datetime(data["InvoiceDate"], errors="coerce")
    max_date = data["InvoiceDate"].max()
    if pd.isna(max_date):
        return 0.0, 0.0
    recent_start = max_date - pd.Timedelta(days=29)
    prior_start = max_date - pd.Timedelta(days=59)
    recent = data[(data["InvoiceDate"] > recent_start)]
    prior = data[(data["InvoiceDate"] <= recent_start) & (data["InvoiceDate"] > prior_start)]
    return float(recent.get("Revenue", pd.Series(dtype=float)).sum()), float(prior.get("Revenue", pd.Series(dtype=float)).sum())


def _build_model_status(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    forecast_metrics = data["forecast_comparison"]
    churn_metrics = data["customer_model_leaderboard"]
    inventory_model = Path(__file__).resolve().parents[1] / "models" / "inventory_risk_model.pkl"
    customer_health_model = Path(__file__).resolve().parents[1] / "models" / "customer_health_model.pkl"
    forecast_model = Path(__file__).resolve().parents[1] / "models" / "best_forecast_model.pkl"
    churn_model = Path(__file__).resolve().parents[1] / "models" / "best_churn_model.pkl"

    forecast_row = (
        forecast_metrics.sort_values(["mape", "rmse"], ascending=[True, True]).head(1)
        if not forecast_metrics.empty and {"mape", "rmse", "model_name"}.issubset(forecast_metrics.columns)
        else pd.DataFrame()
    )
    churn_row = (
        churn_metrics.sort_values(["f1", "balanced_accuracy"], ascending=[False, False]).head(1)
        if not churn_metrics.empty and {"f1", "balanced_accuracy", "model_name"}.issubset(churn_metrics.columns)
        else pd.DataFrame()
    )

    rows: list[dict[str, str]] = []
    if not forecast_row.empty:
        row = forecast_row.iloc[0]
        rows.append(
            {
                "Area": "Demand Forecasting",
                "Artifact": forecast_model.name,
                "Primary Metric": f"MAPE {row['mape']:.3f}",
                "Model": str(row["model_name"]),
                "Status": "Ready",
            }
        )
    if not churn_row.empty:
        row = churn_row.iloc[0]
        rows.append(
            {
                "Area": "Customer Churn",
                "Artifact": churn_model.name,
                "Primary Metric": f"F1 {row['f1']:.3f}",
                "Model": str(row["model_name"]),
                "Status": "Ready",
            }
        )
    rows.extend(
        [
            {
                "Area": "Inventory Optimization",
                "Artifact": inventory_model.name,
                "Primary Metric": "Model file present",
                "Model": "inventory_risk_model",
                "Status": "Ready" if inventory_model.exists() else "Missing",
            },
            {
                "Area": "Customer Health",
                "Artifact": customer_health_model.name,
                "Primary Metric": "Model file present",
                "Model": "customer_health_model",
                "Status": "Ready" if customer_health_model.exists() else "Missing",
            },
        ]
    )
    return pd.DataFrame(rows)


theme_mode = bootstrap_page("AI-Powered Customer Analytics & Demand Forecasting Platform", "📊")
data = load_data_bundle()

sales = data["sales"]
customer_segments = data["customer_segments"]
forecast_results = data["forecast_results"]
inventory_dashboard = data["inventory_dashboard"]
churn_predictions = data["customer_churn_predictions"]
customer_health = data["customer_health_scores"]
forecast_comparison = data["forecast_comparison"]

sidebar_summary = {
    "Revenue": format_currency(sales["Revenue"].sum()) if "Revenue" in sales else "n/a",
    "Customers": format_compact(sales["CustomerID"].nunique()) if "CustomerID" in sales else "n/a",
    "Reports": format_compact(len(list_reports())),
}
render_sidebar(theme_mode=theme_mode, summary=sidebar_summary, page_label="Home")

st.markdown(
    """
<div class="rp-hero">
  <div class="rp-hero-title">RetailPulse – AI-Powered Customer Analytics & Demand Forecasting Platform</div>
  <div class="rp-hero-subtitle">A single Streamlit workspace for executive review, operational monitoring, forecasting, inventory, churn, and report distribution.</div>
</div>
""",
    unsafe_allow_html=True,
)


monthly_sales = _month_series(sales)
recent_revenue, prior_revenue = _compare_recent_periods(sales)
latest_refresh = time_ago(pd.to_datetime(st.session_state.get("rp_last_refresh")))
total_customers = int(sales["CustomerID"].nunique()) if "CustomerID" in sales.columns else 0
total_products = int(sales["Description"].nunique()) if "Description" in sales.columns else 0
forecast_accuracy = calculate_forecast_accuracy(forecast_comparison)
inventory_health = float(inventory_dashboard["InventoryHealthScore"].mean()) if "InventoryHealthScore" in inventory_dashboard.columns else 0.0
churn_rate = float(churn_predictions["ChurnProbability"].mean()) if "ChurnProbability" in churn_predictions.columns else 0.0
customer_health_score = float(customer_health["CustomerHealthScore"].mean()) if "CustomerHealthScore" in customer_health.columns else 0.0

render_kpi_cards(
    [
        KpiCard("Revenue", format_currency(sales["Revenue"].sum()), format_change(recent_revenue, prior_revenue, percent=True), "Last 30 days vs prior 30", "positive" if recent_revenue >= prior_revenue else "warning", "💰"),
        KpiCard("Orders", format_compact(sales["InvoiceNo"].nunique()) if "InvoiceNo" in sales.columns else "n/a", "Unique invoices in the sales fact", "Transaction volume", "neutral", "🧾"),
        KpiCard("Customers", format_compact(total_customers), "Conformed customer count", "Customer base size", "neutral", "👥"),
        KpiCard("Products", format_compact(total_products), "Unique SKUs represented in the platform", "Assortment breadth", "neutral", "📦"),
        KpiCard("Global Forecast Accuracy", f"{forecast_accuracy:.1%}", "Best Overall Forecast Model (evaluated on the complete forecasting dataset)", "Global metric (does not change with filters)", "positive" if forecast_accuracy >= 0.8 else "warning", "🔮"),
        KpiCard("Inventory Health", f"{inventory_health:.1f}", "Average inventory health score", "Operational status", "positive" if inventory_health >= 70 else "warning", "📊"),
        KpiCard("Churn Rate", f"{churn_rate:.1%}", "Average churn probability", "Retention risk", "danger" if churn_rate >= 0.3 else "warning", "🛡️"),
        KpiCard("Customer Health", f"{customer_health_score:.1f}", "Average customer health score", "Portfolio resilience", "positive" if customer_health_score >= 70 else "warning", "❤️"),
    ],
    columns=4,
)

render_section_header("Platform Overview", "Navigation cards and the latest data and model status.")
render_navigation_cards(
    [
        NavigationCard("Executive Dashboard", "Leadership KPIs across revenue, churn, forecast, and inventory.", "pages/01_Executive_Dashboard.py", "📈"),
        NavigationCard("Sales Analytics", "Revenue mix, growth, and basket quality.", "pages/02_Sales_Analytics.py", "💹"),
        NavigationCard("Customer Intelligence", "RFM segments, CLV, and customer health.", "pages/03_Customer_Intelligence.py", "👥"),
        NavigationCard("Demand Forecasting", "Model comparison and future demand planning.", "pages/04_Demand_Forecasting.py", "🔮"),
        NavigationCard("Inventory Optimization", "Replenishment, EOQ, and stock risk.", "pages/05_Inventory_Optimization.py", "📦"),
        NavigationCard("Customer Churn", "Retention actions and SHAP summaries.", "pages/06_Customer_Churn.py", "🛡️"),
        NavigationCard("Report Center", "Download CSV, Markdown, and figure artifacts.", "pages/08_Report_Center.py", "📚"),
        NavigationCard("Settings", "Theme and refresh controls.", "pages/09_Settings.py", "⚙️"),
    ],
    columns=4,
)


left, right = st.columns([1.15, 0.85], gap="large")
with left:
    render_section_header("Sales Trend", "Monthly revenue and order volume from the curated sales fact.")
    if monthly_sales.empty:
        st.info("Sales trend data is not available.")
    else:
        fig = line_chart(monthly_sales, "InvoiceDate", "Revenue", title="Monthly Revenue Trend", mode=theme_mode, height=360, markers=True)
        render_plotly(fig)
with right:
    render_section_header("Customer Mix", "Segment contribution by customer intelligence output.")
    if customer_segments.empty:
        st.info("Customer segment data is not available.")
    else:
        segment_counts = (
            customer_segments.groupby("Segment", dropna=False)
            .agg(Customers=("CustomerID", "nunique"), Revenue=("Revenue", "sum"))
            .reset_index()
            .sort_values("Customers", ascending=False)
        )
        fig = bar_chart(segment_counts, "Segment", "Customers", title="Customers by Segment", mode=theme_mode, height=360)
        render_plotly(fig)

st.divider()
render_section_header("Latest Model Status", "Current model readiness and key leaderboard signal.")
model_status = _build_model_status(data)
if model_status.empty:
    st.info("Model status is not available yet.")
else:
    st.dataframe(model_status, use_container_width=True, hide_index=True)

st.divider()
reports, figures = list_reports(), list_figures()
report_cols = st.columns(2, gap="large")
with report_cols[0]:
    render_section_header("Recent Reports", "Latest markdown deliverables produced by the pipeline.")
    render_artifact_grid(reports[:6], columns=2, download_label="Download report")
with report_cols[1]:
    render_section_header("Generated Figures", "Most recent business figures for quick review.")
    render_artifact_grid(figures[:6], columns=2, download_label="Download figure")

st.divider()
render_section_header("Application Health", f"Theme: {current_theme_mode().title()} · Last refresh: {latest_refresh}")
health_cards = [
    KpiCard("Reports", format_compact(len(reports)), "Markdown deliverables detected", "Report center inventory", "neutral", "📚"),
    KpiCard("Figures", format_compact(len(figures)), "Generated figure assets available", "Figure store", "neutral", "🖼️"),
    KpiCard("Models", format_compact(len(list_models())), "Saved model artifacts available", "Model registry", "neutral", "🧪"),
    KpiCard("Data Bundle", format_compact(len(data)), "Loaded datasets in the current session", "Session cache", "positive", "🗂️"),
]
render_kpi_cards(health_cards, columns=4)
