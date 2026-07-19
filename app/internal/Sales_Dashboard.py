from __future__ import annotations

import streamlit as st

from components.utils import bootstrap_page


bootstrap_page("Legacy Sales Dashboard", "📈")
st.markdown("### Legacy page retained for compatibility")
st.info("Use **Sales Analytics** for the enterprise Streamlit experience.")
st.page_link("pages/02_Sales_Analytics.py", label="Open Sales Analytics", icon="💹")
