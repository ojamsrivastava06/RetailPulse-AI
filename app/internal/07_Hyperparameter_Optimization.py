from __future__ import annotations

import json
from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px

from components.cards import KpiCard, render_kpi_cards, render_section_header
from components.sidebar import render_sidebar
from components.charts import render_plotly
from components.utils import bootstrap_page, format_compact

theme_mode = bootstrap_page("Hyperparameter Optimization", "⚙️")

# File paths
OPTIMIZATION_DIR = Path("reports/optimization")
LEADERBOARD_PATH = OPTIMIZATION_DIR / "leaderboard.csv"
BEST_PARAMS_PATH = OPTIMIZATION_DIR / "best_parameters.json"
HISTORY_PATH = OPTIMIZATION_DIR / "optimization_history.csv"
SUMMARY_PATH = OPTIMIZATION_DIR / "optimization_summary.csv"
IMPORTANCE_PATH = OPTIMIZATION_DIR / "feature_importance.csv"

# Load files
leaderboard_df = pd.DataFrame()
best_params = {}
history_df = pd.DataFrame()
summary_df = pd.DataFrame()
importance_df = pd.DataFrame()

if LEADERBOARD_PATH.exists():
    leaderboard_df = pd.read_csv(LEADERBOARD_PATH)
if BEST_PARAMS_PATH.exists():
    try:
        with open(BEST_PARAMS_PATH, "r") as f:
            best_params = json.load(f)
    except Exception:
        pass
if HISTORY_PATH.exists():
    history_df = pd.read_csv(HISTORY_PATH)
if SUMMARY_PATH.exists():
    summary_df = pd.read_csv(SUMMARY_PATH)
if IMPORTANCE_PATH.exists():
    importance_df = pd.read_csv(IMPORTANCE_PATH)

# Check if data exists
has_data = not leaderboard_df.empty

# Sidebar
best_model = best_params.get("overall_best_model", "n/a")
best_score = best_params.get("overall_best_score", 0.0)

render_sidebar(
    theme_mode=theme_mode,
    page_label="Hyperparameter Optimization",
    summary={
        "Best Model": best_model,
        "Best Score": f"{best_score:.2%}" if best_score > 0 else "n/a",
        "Trials Run": str(len(history_df)) if not history_df.empty else "0",
    },
)

# Title Header
st.markdown(
    """
<div class="rp-hero">
  <div class="rp-hero-title">Hyperparameter Optimization</div>
  <div class="rp-hero-subtitle">Optimize classifier parameters automatically using Optuna and log experiment trials in MLflow.</div>
</div>
""",
    unsafe_allow_html=True,
)

if not has_data:
    st.warning("No hyperparameter optimization results found under `reports/optimization/`.")
    st.info("Run the optimization pipeline using `python src/hyperparameter_optimization.py` to populate this page.")
    
    # Allow running optimization directly from Streamlit for preview/ease of use
    if st.button("Run Hyperparameter Optimization (5 Trials)"):
        with st.spinner("Executing hyperparameter tuning..."):
            try:
                from hyperparameter_optimization import run_hyperparameter_optimization
                run_hyperparameter_optimization(n_trials=5)
                st.success("Optimization executed successfully! Please refresh the page.")
                st.rerun()
            except Exception as e:
                st.error(f"Error running optimization: {e}")
else:
    # 1. KPI Cards
    render_kpi_cards(
        [
            KpiCard("Best Tuned Model", best_model, "Classifier achieving the highest cross-validation score", "Model Leader", "positive", "🏆"),
            KpiCard("Best CV Accuracy", f"{best_score:.2%}", "Stratified 5-fold cross-validation accuracy score", "Metric Score", "positive", "🎯"),
            KpiCard("Total Trials", format_compact(len(history_df)), "Total number of hyperparameter tuning trials", "Study Volume", "neutral", "🔄"),
        ],
        columns=3,
    )
    
    # 2. Leaderboard & Summary
    st.markdown("---")
    left_col, right_col = st.columns([1.2, 0.8], gap="large")
    
    with left_col:
        render_section_header("Tuned Classifiers Leaderboard", "Compare validation accuracy across all optimized classifier architectures.")
        # Render clean leaderboard table
        st.dataframe(
            leaderboard_df[["Model", "BestCVScore", "TuningTrials"]].rename(columns={
                "BestCVScore": "Best CV Accuracy",
                "TuningTrials": "Trials Run"
            }),
            use_container_width=True,
            hide_index=True
        )
        
    with right_col:
        render_section_header("Tuned Parameter Settings", "Detailed hyperparameters chosen for the best classifier.")
        if "overall_best_params" in best_params:
            st.json(best_params["overall_best_params"])
            
    # 3. Plots & Analysis
    st.markdown("---")
    plot_left, plot_right = st.columns([1.0, 1.0], gap="large")
    
    with plot_left:
        render_section_header("Optimization History", "CV score progress over trials for each model type.")
        if not history_df.empty:
            fig_hist = px.line(
                history_df,
                x="Trial",
                y="Value",
                color="Model",
                markers=True,
                labels={"Value": "CV Accuracy", "Trial": "Trial Number"},
                title="Cross-Validation Accuracy Trend"
            )
            fig_hist.update_layout(height=380, margin=dict(l=20, r=20, t=40, b=20))
            render_plotly(fig_hist)
        else:
            st.info("No trial history available.")
            
    with plot_right:
        render_section_header("Trial Distribution", "Validation values vs trial duration scatter.")
        if not history_df.empty:
            fig_scatter = px.scatter(
                history_df,
                x="ExecutionTime",
                y="Value",
                color="Model",
                size="Trial",
                labels={"Value": "CV Accuracy", "ExecutionTime": "Execution Time (s)"},
                title="CV Accuracy vs Execution Time"
            )
            fig_scatter.update_layout(height=380, margin=dict(l=20, r=20, t=40, b=20))
            render_plotly(fig_scatter)
        else:
            st.info("No trial scatter available.")
            
    # 4. Feature Importance
    st.markdown("---")
    imp_left, imp_right = st.columns([1.2, 0.8], gap="large")
    
    with imp_left:
        render_section_header("Tuned Feature Importances", "Feature importances derived from the overall best classifier.")
        if not importance_df.empty:
            fig_imp = px.bar(
                importance_df.sort_values(by="Importance", ascending=True),
                x="Importance",
                y="Feature",
                orientation="h",
                labels={"Importance": "Importance Score", "Feature": "Feature Name"},
                title=f"Feature Importances ({best_model})"
            )
            fig_imp.update_layout(height=380, margin=dict(l=20, r=20, t=40, b=20))
            render_plotly(fig_imp)
        else:
            st.info("Feature importance data is unavailable.")
            
    with imp_right:
        render_section_header("Report Downloads", "Download the pre-saved tuning reports and data files.")
        
        # Download best parameters
        best_params_str = json.dumps(best_params, indent=2)
        st.download_button(
            label="Download Best Parameters (JSON)",
            data=best_params_str,
            file_name="best_parameters.json",
            mime="application/json",
            use_container_width=True
        )
        
        # Download leaderboard
        leaderboard_csv = leaderboard_df.to_csv(index=False)
        st.download_button(
            label="Download Leaderboard (CSV)",
            data=leaderboard_csv,
            file_name="leaderboard.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        # Download history
        history_csv = history_df.to_csv(index=False)
        st.download_button(
            label="Download Trial History (CSV)",
            data=history_csv,
            file_name="optimization_history.csv",
            mime="text/csv",
            use_container_width=True
        )

    # Allow running optimization directly from Streamlit for preview/ease of use
    st.markdown("---")
    st.markdown("### Control Center")
    if st.button("Re-Run Hyperparameter Optimization Study"):
        with st.spinner("Tuning hyperparameters (this may take a few moments)..."):
            try:
                from hyperparameter_optimization import run_hyperparameter_optimization
                run_hyperparameter_optimization(n_trials=5)
                st.success("Optimization executed successfully! Reports generated.")
                st.rerun()
            except Exception as e:
                st.error(f"Error running optimization: {e}")
