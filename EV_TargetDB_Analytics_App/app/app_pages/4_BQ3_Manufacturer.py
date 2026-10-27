from __future__ import annotations

from pathlib import Path

import plotly.express as px
import streamlit as st

from common import get_bq3_manufacturer, get_freshness_timestamp_utc
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
    title="Manufacturer Revenue Ranking",
    subtitle="Which manufacturers generate the highest EV revenue?",
    fetched_at_utc=get_freshness_timestamp_utc(),
    filters=filters,
)

render_section_heading("View Options")
top_n = st.slider("Top manufacturers", min_value=5, max_value=30, value=20, step=1)

try:
    manu = get_bq3_manufacturer(filters)
except RuntimeError as exc:
    render_error_info("BQ3", str(exc))
    st.stop()

if manu.empty:
    render_empty_info("BQ3")
else:
    top = manu.head(top_n)
    fig = px.bar(
        top.sort_values("manufacturer_revenue", ascending=True),
        x="manufacturer_revenue",
        y="manufacturer_name",
        orientation="h",
        hover_data={"market_share_pct": ":.2f"},
        labels={"manufacturer_revenue": "Revenue", "manufacturer_name": "Manufacturer"},
    )
    fig.update_traces(marker_color=PALETTE["accent"])
    st.plotly_chart(apply_chart_style(fig, height=600), width="stretch")

    st.caption(
        "Market share denominator: total manufacturer revenue in the current filtered scope for this page."
    )

render_section_heading("Manufacturer Revenue Data")
display_manu = manu.copy()
display_manu["manufacturer_revenue"] = display_manu["manufacturer_revenue"].map(lambda x: f"${float(x):,.2f}")
display_manu["market_share_pct"] = display_manu["market_share_pct"].map(lambda x: f"{float(x):,.2f}%")
st.dataframe(display_manu, width="stretch", hide_index=True)
