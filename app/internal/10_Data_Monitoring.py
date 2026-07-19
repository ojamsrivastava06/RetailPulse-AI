from __future__ import annotations

import json
from pathlib import Path
import pandas as pd
import streamlit as st

from components.cards import KpiCard, render_kpi_cards, render_section_header
from components.sidebar import render_sidebar
from components.utils import bootstrap_page, format_compact, read_text

theme_mode = bootstrap_page("Data Monitoring", "📊")

MONITORING_DIR = Path("reports/evidently")
DRIFT_SUMMARY_JSON = MONITORING_DIR / "drift_summary.json"
DRIFT_SUMMARY_CSV = MONITORING_DIR / "drift_summary.csv"
DRIFT_REPORT_HTML = MONITORING_DIR / "data_drift_report.html"
QUALITY_REPORT_HTML = MONITORING_DIR / "data_quality_report.html"

# Load files
summary_data = {}
feature_drift_df = pd.DataFrame()

if DRIFT_SUMMARY_JSON.exists():
    try:
        with open(DRIFT_SUMMARY_JSON, "r") as f:
            summary_data = json.load(f)
    except Exception:
        pass
if DRIFT_SUMMARY_CSV.exists():
    feature_drift_df = pd.read_csv(DRIFT_SUMMARY_CSV)

# Check if data exists
has_data = bool(summary_data)

# KPI / Sidebar Data
drift_summary = summary_data.get("drift_summary", {})
quality_summary = summary_data.get("quality_summary", {})
feature_drift = summary_data.get("feature_drift", {})

drift_count = drift_summary.get("drift_count", 0)
drift_share = drift_summary.get("drift_share", 0.0)
dataset_drifted = drift_summary.get("dataset_drifted", False)
row_count = quality_summary.get("row_count", 0)
missing_values_count = quality_summary.get("missing_values_count", 0)
missing_values_share = quality_summary.get("missing_values_share", 0.0)

drift_status_str = "Drift Detected" if dataset_drifted else "No Drift Detected"
drift_status_type = "negative" if dataset_drifted else "positive"

render_sidebar(
    theme_mode=theme_mode,
    page_label="Data Monitoring",
    summary={
        "Drift Status": drift_status_str,
        "Drifted Share": f"{drift_share:.1%}" if has_data else "n/a",
        "Missing Values": f"{missing_values_share:.2%}" if has_data else "n/a",
    },
)

# Title Header
st.markdown(
    """
<div class="rp-hero">
  <div class="rp-hero-title">Data Monitoring & Drift Detection</div>
  <div class="rp-hero-subtitle">Monitor data consistency, detect statistical feature drift, and analyze dataset quality using Evidently AI and MLflow.</div>
</div>
""",
    unsafe_allow_html=True,
)

if not has_data:
    st.warning("No data monitoring results found under `reports/evidently/`.")
    st.info("Run the monitoring pipeline to compare the reference dataset with the latest processed dataset.")
    
    if st.button("Run Data Monitoring & Drift Detection"):
        with st.spinner("Analyzing datasets for drift and quality..."):
            try:
                from data_monitoring import run_data_monitoring
                run_data_monitoring()
                st.success("Data monitoring executed successfully! Please refresh the page.")
                st.rerun()
            except Exception as e:
                st.error(f"Error running data monitoring: {e}")
else:
    # 1. KPI Cards
    render_kpi_cards(
        [
            KpiCard(
                label="Drift Status",
                value=drift_status_str,
                note="Significant statistical drift detected across features" if dataset_drifted else "Features are statistically stable",
                status=drift_status_type,
                icon="⚠️" if dataset_drifted else "✅"
            ),
            KpiCard(
                label="Drifted Features",
                value=f"{int(drift_count)} / {len(feature_drift)}",
                note=f"Share of drifted features: {drift_share:.1%}",
                status="warning" if drift_count > 0 else "positive",
                icon="📊"
            ),
            KpiCard(
                label="Dataset Size",
                value=format_compact(row_count),
                note="Total transaction rows evaluated",
                status="neutral",
                icon="📈"
            ),
            KpiCard(
                label="Missing Values",
                value=f"{missing_values_share:.2%}",
                note=f"Total nulls: {format_compact(missing_values_count)}",
                status="warning" if missing_values_share > 0.01 else "positive",
                icon="❓"
            ),
        ],
        columns=4,
    )
    
    # Tabs for different views
    tabs = st.tabs(["Overview", "Feature Drift Summary", "Interactive Drift Report", "Interactive Quality Report"])
    
    with tabs[0]:
        st.markdown("---")
        render_section_header("Monitoring Overview", "Summary of data stability and quality checks.")
        
        # Display dataset info
        info_col1, info_col2 = st.columns(2, gap="large")
        with info_col1:
            st.markdown("#### Dataset Metrics")
            st.write(f"- **Reference Dataset size:** 50% of historical processed dataset")
            st.write(f"- **Current/Latest Dataset size:** 50% of historical processed dataset")
            st.write(f"- **Total Rows Monitored:** {int(row_count):,}")
            st.write(f"- **Total Columns Monitored:** {quality_summary.get('column_count', 'n/a')}")
            st.write(f"- **Duplicated Rows:** {int(quality_summary.get('duplicated_rows_count', 0)):,}")
            
        with info_col2:
            st.markdown("#### Stability Summary")
            st.write(f"- **Drifted Features count:** {int(drift_count)}")
            st.write(f"- **Stable Features count:** {len(feature_drift) - int(drift_count)}")
            st.write(f"- **Overall Status:** {'⚠️ Warning: Dataset has drifted significantly' if dataset_drifted else '✅ Pass: Dataset statistics are stable'}")
            
        st.markdown("---")
        st.markdown("### Control Center")
        if st.button("Re-Run Data Monitoring & Drift Detection"):
            st.spinner("Analyzing datasets for drift and quality...")
            try:
                from data_monitoring import run_data_monitoring
                run_data_monitoring()
                st.success("Data monitoring executed successfully! Reports updated.")
                st.rerun()
            except Exception as e:
                st.error(f"Error running data monitoring: {e}")
                    
    with tabs[1]:
        st.markdown("---")
        render_section_header("Feature Drift Summary", "Detailed drift statistics per feature using statistical significance tests.")
        
        if not feature_drift_df.empty:
            # Format dataframe for display
            display_df = feature_drift_df.copy()
            display_df["drifted"] = display_df["drifted"].map({1: "⚠️ Drifted", 0: "✅ Stable"})
            display_df = display_df.rename(columns={
                "feature": "Feature Name",
                "p_value": "p-value",
                "threshold": "Significance Threshold",
                "drifted": "Drift Status"
            })
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No feature drift details available.")
            
    with tabs[2]:
        st.markdown("---")
        render_section_header("Evidently AI - Data Drift Interactive Report", "Full interactive dashboard of statistical tests run across features.")
        if DRIFT_REPORT_HTML.exists():
            html_content = read_text(DRIFT_REPORT_HTML)
            st.components.v1.html(html_content, height=800, scrolling=True)
        else:
            st.error("Data Drift HTML report not found.")
            
    with tabs[3]:
        st.markdown("---")
        render_section_header("Evidently AI - Data Quality Interactive Report", "Full interactive dashboard of descriptive statistics and missing values.")
        if QUALITY_REPORT_HTML.exists():
            html_content = read_text(QUALITY_REPORT_HTML)
            st.components.v1.html(html_content, height=800, scrolling=True)
        else:
            st.error("Data Quality HTML report not found.")
