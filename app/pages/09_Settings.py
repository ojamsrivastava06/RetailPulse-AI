from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from components.cards import KpiCard, render_kpi_cards, render_section_header, status_pill
from components.sidebar import render_sidebar
from components.tables import render_dataframe
from components.utils import (
    REFRESH_KEY,
    bootstrap_page,
    current_theme_mode,
    format_compact,
    list_models,
    load_data_bundle,
    set_theme_mode,
)


theme_mode = bootstrap_page("Settings", "⚙️")
data = load_data_bundle()

render_sidebar(
    theme_mode=theme_mode,
    page_label="Settings",
    summary={
        "Theme": current_theme_mode().title(),
        "Models": format_compact(len(list_models())),
    },
)

st.markdown(
    """
<div class="rp-hero">
  <div class="rp-hero-title">Settings</div>
  <div class="rp-hero-subtitle">Control the application theme, refresh cached data, and review platform metadata.</div>
</div>
""",
    unsafe_allow_html=True,
)

st.subheader("Theme Selector")
theme_choice = st.radio("Theme mode", ["Dark", "Light"], index=0 if current_theme_mode() == "dark" else 1, horizontal=True)
selected_theme = theme_choice.lower()
if selected_theme != current_theme_mode():
    set_theme_mode(selected_theme)
    st.success(f"Theme updated to {theme_choice.lower()}.")
    st.rerun()

st.divider()
st.subheader("Data Refresh")
st.caption("Refresh clears the Streamlit cache and reloads the already-processed CSV artifacts. It does not rerun the ML pipeline.")
if st.button("Refresh cached data", type="primary"):
    st.cache_data.clear()
    st.session_state[REFRESH_KEY] = datetime.now(timezone.utc).isoformat()
    st.success("Data cache cleared and timestamp refreshed.")
    st.rerun()

st.divider()
st.subheader("Application Information")
render_kpi_cards(
    [
        KpiCard("Models", format_compact(len(list_models())), "Saved model artifacts available", "Model inventory", "neutral", "🧪"),
        KpiCard("Datasets", format_compact(len(data)), "Loaded dataset bundle size", "Session load", "positive", "🗂️"),
    ],
    columns=2,
)

info = pd.DataFrame(
    [
        {"Setting": "Theme", "Value": current_theme_mode().title()},
        {"Setting": "Last refresh", "Value": st.session_state.get(REFRESH_KEY, "n/a")},
        {"Setting": "Models directory", "Value": str(list_models()[0].path.parent) if list_models() else "n/a"},
        {"Setting": "Data bundle size", "Value": format_compact(len(data))},
    ]
)
render_dataframe(info, height=260)

st.divider()
st.markdown(status_pill("Streamlit platform ready", "success"), unsafe_allow_html=True)

