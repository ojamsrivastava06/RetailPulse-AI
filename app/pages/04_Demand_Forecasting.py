from __future__ import annotations

import pandas as pd
import streamlit as st

from components.cards import KpiCard, render_kpi_cards, render_section_header
from components.charts import bar_chart, line_chart, render_plotly, scatter_chart
from components.filters import render_filter_bar
from components.sidebar import render_sidebar
from components.tables import render_dataframe
from components.utils import bootstrap_page, format_compact, format_currency, load_data_bundle, calculate_forecast_accuracy, filter_forecast_comparison


def _normalize_forecast(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    if "Date" in data.columns:
        data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    return data


theme_mode = bootstrap_page("Demand Forecasting", "🔮")
data = load_data_bundle()

forecast_results = _normalize_forecast(data["forecast_results"])
future_predictions = _normalize_forecast(data["future_predictions"])
forecast_metrics = data["forecast_metrics"]
forecast_comparison = data["forecast_comparison"]
forecast_dashboard = data["forecast_dashboard"]

render_sidebar(
    theme_mode=theme_mode,
    page_label="Demand Forecasting",
    summary={
        "Global Accuracy": f"{calculate_forecast_accuracy(forecast_comparison):.1%}" if not forecast_comparison.empty else "n/a",

        "Series": format_compact(forecast_results["SeriesKey"].nunique()) if "SeriesKey" in forecast_results.columns else "n/a",
        "Models": format_compact(forecast_results["Model"].nunique()) if "Model" in forecast_results.columns else "n/a",
    },
)

st.markdown(
    """
<div class="rp-hero">
  <div class="rp-hero-title">Demand Forecasting</div>
  <div class="rp-hero-subtitle">Compare backtests, future predictions, and model quality across products and markets.</div>
</div>
""",
    unsafe_allow_html=True,
)

with st.container(border=True):
    render_section_header("Forecast Filters", "Use model, product, country, and category filters to isolate a forecast story.")
    forecast_results, selections = render_filter_bar(
        forecast_results,
        date_column="Date",
        categorical_columns=["Model", "Product", "Country", "ProductCategory"],
        key_prefix="forecast",
    )

selected_model = selections.get("Model", [])
selected_product = selections.get("Product", [])
selected_country = selections.get("Country", [])
selected_category = selections.get("ProductCategory", [])

future_view = future_predictions.copy()
for column, selection in [
    ("Model", selected_model),
    ("Product", selected_product),
    ("Country", selected_country),
    ("ProductCategory", selected_category),
]:
    if selection and column in future_view.columns:
        future_view = future_view[future_view[column].astype(str).isin(selection)]

horizon_values = sorted(future_view["HorizonDays"].dropna().astype(int).unique().tolist()) if "HorizonDays" in future_view.columns and not future_view.empty else []
selected_horizon = st.selectbox("Forecast Horizon", horizon_values or [30, 60, 90, 180], index=0)
if "HorizonDays" in future_view.columns:
    future_view = future_view[future_view["HorizonDays"] == selected_horizon]

forecast_eval = forecast_results.copy()
forecast_eval = forecast_eval.dropna(subset=["Date"]) if "Date" in forecast_eval.columns else forecast_eval
future_view = future_view.dropna(subset=["Date"]) if "Date" in future_view.columns else future_view

monthly_eval = (
    forecast_eval.groupby(pd.Grouper(key="Date", freq="ME"))
    .agg(Actual=("Actual", "sum"), Forecast=("Forecast", "sum"), Residual=("Residual", "sum"))
    .reset_index()
    if not forecast_eval.empty and "Date" in forecast_eval.columns
    else pd.DataFrame(columns=["Date", "Actual", "Forecast", "Residual"])
)
future_series = (
    future_view.groupby("Date").agg(ForecastDemand=("ForecastDemand", "sum"), ForecastRevenue=("ForecastRevenue", "sum")).reset_index()
    if not future_view.empty and "Date" in future_view.columns
    else pd.DataFrame(columns=["Date", "ForecastDemand", "ForecastRevenue"])
)
filtered_comp = filter_forecast_comparison(forecast_comparison, selections)
comparison = filtered_comp.sort_values(["mape", "rmse"], ascending=[True, True]).head(12) if not filtered_comp.empty else pd.DataFrame()
metric_rows = forecast_metrics.sort_values(["mape", "rmse"], ascending=[True, True]).head(20) if not forecast_metrics.empty else pd.DataFrame()
dashboard_view = forecast_dashboard.sort_values("ForecastRevenue", ascending=False) if "ForecastRevenue" in forecast_dashboard.columns else forecast_dashboard

render_kpi_cards(
    [
        KpiCard("Forecast Revenue", format_currency(future_view["ForecastRevenue"].sum()) if "ForecastRevenue" in future_view.columns else "n/a", "Future revenue value in the current context", "Planning value", "positive", "💰"),
        KpiCard("Forecast Demand", format_compact(future_view["ForecastDemand"].sum()) if "ForecastDemand" in future_view.columns else "n/a", "Future demand volume", "Planning volume", "neutral", "📦"),
        KpiCard("Global Forecast Accuracy", f"{calculate_forecast_accuracy(filtered_comp):.1%}" if not filtered_comp.empty else "n/a", "Best Overall Forecast Model (evaluated on the complete forecasting dataset)", "Global metric (does not change with filters)", "positive", "🎯"),
        KpiCard("MAPE", f"{(float(filtered_comp['mape'].min()) / 100.0):.2%}" if not filtered_comp.empty else "n/a", "Lowest mean absolute percentage error", "Error rate", "warning", "📉"),
        KpiCard("Forecast Error", format_currency(forecast_eval["Residual"].sum()) if "Residual" in forecast_eval.columns else "n/a", "Signed residual from the backtest", "Bias", "neutral", "🧪"),
        KpiCard("Best Model Count", format_compact(len(comparison)), "Models compared in the selected context", "Model coverage", "neutral", "🏆"),
    ],
    columns=3,
)

top = st.columns([1.15, 0.85], gap="large")
with top[0]:
    render_section_header("Backtest", "Actual versus forecast in the historical evaluation window.")
    if monthly_eval.empty:
        st.info("Forecast backtest data is unavailable.")
    else:
        fig = line_chart(monthly_eval, "Date", "Actual", title="Actual vs Forecast", mode=theme_mode, height=360, markers=True)
        if "Forecast" in monthly_eval.columns:
            fig.add_scatter(x=monthly_eval["Date"], y=monthly_eval["Forecast"], mode="lines", name="Forecast")
        render_plotly(fig)
with top[1]:
    render_section_header("Future Outlook", "Forecast demand and revenue for the selected horizon.")
    if future_series.empty:
        st.info("Future predictions are unavailable.")
    else:
        fig = line_chart(future_series, "Date", "ForecastDemand", title="Future Demand", mode=theme_mode, height=360, markers=True)
        render_plotly(fig)

bottom_left, bottom_right = st.columns([1, 1], gap="large")
with bottom_left:
    render_section_header("Model Comparison", "Top forecast models ranked by error.")
    if comparison.empty:
        st.info("Forecast comparison data is unavailable.")
    else:
        fig = bar_chart(comparison, "model_name", "mape", title="MAPE by Model", mode=theme_mode, height=330)
        render_plotly(fig)
with bottom_right:
    render_section_header("Residual Diagnostics", "Error spread across the selected forecast context.")
    if monthly_eval.empty:
        st.info("Residual diagnostics are unavailable.")
    else:
        fig = scatter_chart(monthly_eval, "Actual", "Residual", size="Forecast", title="Residual Diagnostics", mode=theme_mode, height=330)
        render_plotly(fig)

st.divider()
render_section_header("Forecast Detail", "Forecast dashboard and leaderboard outputs from the pipeline.")
detail_tabs = st.tabs(["Dashboard", "Comparison", "Metrics"])
with detail_tabs[0]:
    render_dataframe(dashboard_view.head(25), height=280)
with detail_tabs[1]:
    render_dataframe(comparison, height=280)
with detail_tabs[2]:
    render_dataframe(metric_rows, height=280)
