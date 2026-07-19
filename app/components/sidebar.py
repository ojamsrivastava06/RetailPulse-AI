from __future__ import annotations

from pathlib import Path
from typing import Mapping

import streamlit as st

from components.cards import status_pill
from components.utils import APP_ROOT, LOGO_PATH, PAGE_LINKS


def render_sidebar(
    *,
    theme_mode: str,
    summary: Mapping[str, str] | None = None,
    page_label: str | None = None,
) -> None:
    with st.sidebar:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=84)
        st.markdown("<div class='rp-sidebar-brand'>RetailPulse</div>", unsafe_allow_html=True)
        st.caption("AI-Powered Customer Analytics & Demand Forecasting Platform")

        st.markdown(status_pill(f"Theme: {theme_mode.title()}", "neutral"), unsafe_allow_html=True)
        if page_label:
            st.caption(f"Current page: {page_label}")
        if summary:
            st.divider()
            for label, value in summary.items():
                st.metric(label, value)
        st.divider()
        st.markdown("**Navigation**")
        for link in PAGE_LINKS:
            st.page_link(link.path, label=link.label, icon=link.icon)
        st.divider()
        st.caption(f"Project root: {APP_ROOT.name}")

