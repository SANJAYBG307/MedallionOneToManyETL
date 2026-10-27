from __future__ import annotations

from pathlib import Path

import plotly.express as px
import streamlit as st

from common import get_bq1_trend_by_grain, get_freshness_timestamp_utc
from ui import (
    PALETTE,
    apply_chart_style,
    apply_theme,
    get_active_filters,
    render_empty_info,
    render_error_info,
    render_header,
    render_section_heading,
)


APP_FAVICON = str(Path(__file__).resolve().parents[1] / "assets" / "ev_domain_icon.svg")
APP_TITLE = "EV Intelligence Dashboard"


st.set_page_config(page_title=APP_TITLE, page_icon=APP_FAVICON, layout="wide")
apply_theme()
filters = get_active_filters()

render_header(
    title="EV Transaction Trend Over Time",
    subtitle="How has EV transaction volume changed over time?",
    fetched_at_utc=get_freshness_timestamp_utc(),
    filters=filters,
)

render_section_heading("View Options")
grain = st.segmented_control(
    "Trend granularity",
    options=["month", "year", "day"],
    default="month",
    format_func=lambda g: {"month": "Monthly", "year": "Yearly", "day": "Daily"}[g],
)

try:
    trend = get_bq1_trend_by_grain(filters, grain=grain or "month")
except RuntimeError as exc:
    render_error_info("BQ1", str(exc))
    st.stop()

if trend.empty:
    render_empty_info("BQ1")
else:
    fig = px.line(
        trend,
        x="period_start",
        y="total_transactions",
        markers=True,
        labels={"period_start": "Period", "total_transactions": "Distinct Transactions"},
    )
    fig.update_traces(line_color=PALETTE["accent"], marker_color=PALETTE["accent_dark"])
    st.plotly_chart(apply_chart_style(fig, height=470), width="stretch")

    if len(trend) >= 2:
        latest = float(trend.iloc[-1]["total_transactions"])
        prior = float(trend.iloc[-2]["total_transactions"])
        delta = latest - prior
        delta_pct = (delta / prior * 100) if prior > 0 else 0.0
        c1, c2 = st.columns(2)
        c1.metric("Latest period transactions", f"{latest:,.0f}", f"{delta:,.0f}")
        c2.metric("Period-over-period change", f"{delta_pct:,.2f}%")

render_section_heading("Trend Data")
st.dataframe(trend, width="stretch", hide_index=True)
