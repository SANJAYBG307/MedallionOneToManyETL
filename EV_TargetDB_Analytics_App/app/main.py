from __future__ import annotations

from pathlib import Path

import streamlit as st

from ui import render_filter_sidebar

APP_FAVICON = str(Path(__file__).resolve().parent / "assets" / "ev_domain_icon.svg")
APP_TITLE = "EV Intelligence Dashboard"

st.set_page_config(page_title=APP_TITLE, page_icon=APP_FAVICON, layout="wide")

# Use main.py as a router only so analytics pages are KPI/BQ-focused.
nav = st.navigation(
    [
        st.Page("app_pages/0_EV_Domain_Context.py", title="EV Domain", icon=":material/electric_car:", url_path="ev-domain"),
        st.Page("app_pages/1_KPI_Overview.py", title="KPI Overview", icon=":material/monitoring:", url_path="kpi-overview"),
        st.Page("app_pages/2_BQ1_Trend.py", title="Trend", icon=":material/show_chart:", url_path="trend"),
        st.Page("app_pages/3_BQ2_Geography.py", title="Geography", icon=":material/public:", url_path="geography"),
        st.Page("app_pages/4_BQ3_Manufacturer.py", title="Manufacturer", icon=":material/factory:", url_path="manufacturer"),
        st.Page("app_pages/5_BQ4_Models.py", title="Models", icon=":material/directions_car:", url_path="models"),
        st.Page("app_pages/6_BQ5_Activity_Share.py", title="Activity Share", icon=":material/donut_small:", url_path="activity-share"),
    ],
    position="sidebar",
)

# Render global filters after navigation is registered so custom page labels appear immediately.
render_filter_sidebar()
nav.run()
