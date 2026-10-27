from __future__ import annotations

from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from common import get_bq5_activity_share, get_freshness_timestamp_utc
from ui import apply_chart_style, apply_theme, get_active_filters, render_empty_info, render_error_info, render_header, render_section_heading


APP_FAVICON = str(Path(__file__).resolve().parents[1] / "assets" / "ev_domain_icon.svg")
APP_TITLE = "EV Intelligence Dashboard"


st.set_page_config(page_title=APP_TITLE, page_icon=APP_FAVICON, layout="wide")
apply_theme()
filters = get_active_filters()

activity_colors = {
    "Charging": "#0F9D91",
    "Production": "#102A43",
    "Sale": "#243B53",
    "Service": "#74C69D",
    "Unknown": "#A0AEC0",
}

try:
    activity = get_bq5_activity_share(filters)
except RuntimeError as exc:
    render_error_info("BQ5", str(exc))
    st.stop()

render_header(
    title="Activity Share Distribution",
    subtitle="What is the activity share across Charging, Production, Sale, and Service?",
    fetched_at_utc=get_freshness_timestamp_utc(),
    filters=filters,
)

render_section_heading("View Options")
st.caption("This page uses the active global filters from the sidebar.")

if activity.empty:
    render_empty_info("BQ5")
else:
    colors = [activity_colors.get(str(name), "#CBD5E0") for name in activity["activity_type"]]
    fig = go.Figure(
        data=[
            go.Pie(
                labels=activity["activity_type"],
                values=activity["total_transactions"],
                hole=0.6,
                textinfo="percent+label",
                marker=dict(colors=colors, line=dict(color="#FFFFFF", width=1.5)),
            )
        ]
    )
    st.plotly_chart(apply_chart_style(fig, height=520, show_legend=True), width="stretch")

    st.caption(
        "Shares are computed as distinct transactions per activity over total distinct transactions in scope; totals can exceed 100% when a transaction belongs to multiple activities."
    )

render_section_heading("Activity Mix Data")
display_activity = activity.copy()
display_activity["activity_share_pct"] = display_activity["activity_share_pct"].map(lambda x: f"{float(x):,.2f}%")
display_activity["total_transactions"] = display_activity["total_transactions"].map(lambda x: f"{int(x):,}")
st.dataframe(display_activity, width="stretch", hide_index=True)
