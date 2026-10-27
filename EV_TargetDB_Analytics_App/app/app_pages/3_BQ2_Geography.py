from __future__ import annotations

from pathlib import Path

import plotly.express as px
import streamlit as st

from common import get_bq2_geography, get_freshness_timestamp_utc
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
    title="States and Cities with Highest EV Activity",
    subtitle="Which states and cities have the highest EV activity?",
    fetched_at_utc=get_freshness_timestamp_utc(),
    filters=filters,
)

render_section_heading("View Options")
analysis_level = st.segmented_control(
    "Analyze by",
    options=["state", "city"],
    default="state",
    format_func=lambda x: "State ranking" if x == "state" else "City ranking",
)
top_n = st.slider("Top N", min_value=5, max_value=30, value=15, step=1)

try:
    geo = get_bq2_geography(filters)
except RuntimeError as exc:
    render_error_info("BQ2", str(exc))
    st.stop()

if geo.empty:
    render_empty_info("BQ2")
else:
    state_rank = (
        geo.groupby("state", as_index=False)["total_transactions"]
        .sum()
        .sort_values("total_transactions", ascending=False)
    )
    city_rank = geo.sort_values("total_transactions", ascending=False)

    rank_df = state_rank if analysis_level == "state" else city_rank
    rank_col = "state" if analysis_level == "state" else "city"
    chart_df = rank_df.head(top_n).sort_values("total_transactions", ascending=True)

    render_section_heading(f"Top {top_n} by {rank_col.title()}")
    fig = px.bar(
        chart_df,
        x="total_transactions",
        y=rank_col,
        orientation="h",
        labels={"total_transactions": "Distinct Transactions", rank_col: rank_col.title()},
        hover_data={"total_transactions": ":,.0f"},
    )
    fig.update_traces(marker_color=PALETTE["accent"])
    st.plotly_chart(apply_chart_style(fig, height=560), width="stretch")

    render_section_heading("Supporting Geography Data")
    st.dataframe(rank_df, width="stretch", hide_index=True)
