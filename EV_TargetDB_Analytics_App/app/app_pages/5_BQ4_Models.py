from __future__ import annotations

from pathlib import Path

import plotly.express as px
import streamlit as st

from common import get_bq4_models, get_freshness_timestamp_utc
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


def _short_label(value: str, max_len: int = 28) -> str:
    text = str(value)
    return text if len(text) <= max_len else text[: max_len - 3] + "..."


st.set_page_config(page_title=APP_TITLE, page_icon=APP_FAVICON, layout="wide")
apply_theme()
filters = get_active_filters()

render_header(
    title="Top EV Models by Transaction Count",
    subtitle="Which EV models are most popular by transaction count?",
    fetched_at_utc=get_freshness_timestamp_utc(),
    filters=filters,
)

render_section_heading("View Options")
top_n = st.slider("Top models", min_value=5, max_value=40, value=20, step=1)

try:
    models = get_bq4_models(filters)
except RuntimeError as exc:
    render_error_info("BQ4", str(exc))
    st.stop()

if models.empty:
    render_empty_info("BQ4")
else:
    top = models.head(top_n).copy()
    top["model_name_short"] = top["model_name"].map(_short_label)
    fig = px.bar(
        top.sort_values("total_transactions", ascending=True),
        x="total_transactions",
        y="model_name_short",
        orientation="h",
        labels={"total_transactions": "Distinct Transactions", "model_name_short": "EV Model"},
        hover_data={"model_name": True, "total_transactions": ":,.0f"},
    )
    fig.update_traces(marker_color=PALETTE["accent"])
    st.plotly_chart(apply_chart_style(fig, height=620), width="stretch")

render_section_heading("Model Popularity Data")
st.dataframe(models, width="stretch", hide_index=True)
