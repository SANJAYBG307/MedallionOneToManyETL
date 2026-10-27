from __future__ import annotations

from pathlib import Path

import streamlit as st

from common import get_bq5_activity_share, get_freshness_timestamp_utc, get_kpis
from ui import apply_theme, get_active_filters, render_error_info, render_header, render_section_heading


ICON_SVG = Path(__file__).resolve().parents[1] / "assets" / "ev_domain_icon.svg"
APP_FAVICON = str(ICON_SVG)
APP_TITLE = "EV Intelligence Dashboard"
EV_ICON_MARKUP = ICON_SVG.read_text(encoding="utf-8") if ICON_SVG.exists() else ""


st.set_page_config(page_title=APP_TITLE, page_icon=APP_FAVICON, layout="wide")
apply_theme()
filters = get_active_filters()

try:
    kpis = get_kpis(filters)
    activity = get_bq5_activity_share(filters)
except RuntimeError as exc:
    render_error_info("EV Domain Context", str(exc))
    st.stop()


def _kpi_value(kpi_id: str) -> float:
    row = kpis.loc[kpis["kpi_id"] == kpi_id, "value"]
    if row.empty:
        return 0.0
    return float(row.iloc[0] or 0.0)


total_txn = int(_kpi_value("KPI1"))
total_revenue = float(_kpi_value("KPI2"))
avg_sale_price = float(_kpi_value("KPI3"))
warranty_rate = float(_kpi_value("KPI5"))

top_activity = "N/A"
top_activity_share = 0.0
if not activity.empty:
    top_activity = str(activity.iloc[0].get("activity_type", "N/A"))
    top_activity_share = float(activity.iloc[0].get("activity_share_pct", 0.0) or 0.0)

render_header(
    title="EV Domain Context",
    subtitle="Business framing for the EV lifecycle and current in-scope operational snapshot.",
    fetched_at_utc=get_freshness_timestamp_utc(),
    filters=filters,
)

render_section_heading("EV Ecosystem Overview")
with st.container(border=True):
    icon_col, text_col = st.columns([1, 12], vertical_alignment="center")
    with icon_col:
        if ICON_SVG.exists():
            st.image(str(ICON_SVG), width=28)
    with text_col:
        st.markdown("**How to read this domain context**")

    st.markdown(
        "The EV ecosystem spans Charging, Production, Sale, and Service activities. "
        "Performance at each stage affects customer demand, pricing outcomes, manufacturer competitiveness, "
        "and long-term ownership experience."
    )
    st.markdown(
        "This analytics suite tracks EV transaction flow and monetization quality through KPI1-KPI5, then supports "
        "drill-down through BQ1-BQ5 for trend, geography, manufacturer, model, and activity-share diagnostics."
    )
    st.markdown("Use this page first for business context, then move to KPI Overview and other pages for analysis.")

render_section_heading("Current Data Snapshot (Active Filters)")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Distinct EV transactions", f"{total_txn:,}")
m2.metric("Total EV revenue", f"${total_revenue:,.2f}")
m3.metric("Avg selling price (Sale)", f"${avg_sale_price:,.2f}")
m4.metric("Warranty claim rate", f"{warranty_rate:,.2f}%")
m5.metric("Highest activity share", f"{top_activity}", f"{top_activity_share:,.2f}%")
