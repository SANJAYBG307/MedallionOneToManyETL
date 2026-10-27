from __future__ import annotations

from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from common import get_bq1_trend_by_grain, get_bq5_activity_share, get_detail_rows, get_freshness_timestamp_utc, get_kpis
from ui import (
    PALETTE,
    apply_chart_style,
    apply_theme,
    get_active_filters,
    render_error_info,
    render_header,
    render_kpi_cards,
    render_section_heading,
)


APP_FAVICON = str(Path(__file__).resolve().parents[1] / "assets" / "ev_domain_icon.svg")
APP_TITLE = "EV Intelligence Dashboard"


st.set_page_config(page_title=APP_TITLE, page_icon=APP_FAVICON, layout="wide")
apply_theme()
filters = get_active_filters()

try:
    kpis = get_kpis(filters)
    trend = get_bq1_trend_by_grain(filters, grain="month")
    activity = get_bq5_activity_share(filters)
except RuntimeError as exc:
    render_error_info("KPI Overview", str(exc))
    st.stop()

render_header(
    title="KPI Overview",
    subtitle="Executive summary of EV transactions, revenue, pricing, market share, and warranty outcomes.",
    fetched_at_utc=get_freshness_timestamp_utc(),
    filters=filters,
)

render_kpi_cards(kpis)

left, right = st.columns([1.3, 1])
with left:
    render_section_heading("Monthly Transaction Trend")
    if trend.empty:
        st.info("No monthly trend data available.")
    else:
        fig_trend = px.line(
            trend,
            x="period_start",
            y="total_transactions",
            markers=True,
            labels={"period_start": "Month", "total_transactions": "Distinct Transactions"},
        )
        fig_trend.update_traces(line_color=PALETTE["accent"], marker_color=PALETTE["accent_dark"])
        st.plotly_chart(apply_chart_style(fig_trend, height=330), width="stretch")

with right:
    render_section_heading("Activity Mix Snapshot")
    if activity.empty:
        st.info("No activity mix data available.")
    else:
        fig_activity = go.Figure(
            data=[
                go.Pie(
                    labels=activity["activity_type"],
                    values=activity["total_transactions"],
                    hole=0.62,
                    textinfo="percent+label",
                    marker=dict(
                        colors=["#0F9D91", "#102A43", "#243B53", "#74C69D", "#A0AEC0"],
                        line=dict(color="#FFFFFF", width=1.5),
                    ),
                )
            ]
        )
        st.plotly_chart(apply_chart_style(fig_activity, height=330, show_legend=False), width="stretch")

render_section_heading("KPI Details")
st.dataframe(kpis, width="stretch", hide_index=True)

render_section_heading("Filtered Data Extract")
load_detail = st.toggle("Load detailed rows", value=False, help="Loads up to 3,000 rows for export and inspection.")
if load_detail:
    detail = get_detail_rows(filters, limit=3000)
    st.dataframe(detail, width="stretch", height=340)
    if not detail.empty:
        st.download_button(
            label="Download filtered detail (CSV)",
            data=detail.to_csv(index=False).encode("utf-8"),
            file_name="kpi_filtered_detail.csv",
            mime="text/csv",
        )
else:
    st.info("Enable 'Load detailed rows' to fetch the filtered detail dataset.")
