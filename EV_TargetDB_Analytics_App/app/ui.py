from __future__ import annotations

from datetime import timezone
from pathlib import Path
from typing import Iterable

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from common import CACHE_TTL_SECONDS, FilterContext, get_data_date_range, get_dimension_options


PALETTE = {
    "bg": "#F4F7FA",
    "card": "#FFFFFF",
    "primary": "#102A43",
    "secondary": "#243B53",
    "accent": "#0F9D91",
    "accent_dark": "#087F78",
    "muted": "#627D98",
    "border": "#E2E8F0",
}


def get_app_favicon() -> str:
  icon_path = Path(__file__).resolve().parent / "assets" / "ev_domain_icon.svg"
  return str(icon_path)


def apply_theme() -> None:
    st.markdown(
        """
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

          :root {
            --bg: #F4F7FA;
            --surface: #FFFFFF;
            --text: #102A43;
            --text-soft: #627D98;
            --text-secondary: #243B53;
            --accent: #0F9D91;
            --accent-dark: #087F78;
            --border: #E2E8F0;
            --shadow: 0 2px 8px rgba(16, 42, 67, 0.07);
          }

          html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
          .stApp { background: var(--bg); color: var(--text); }

          .main .block-container {
            padding-top: 1.15rem;
            padding-bottom: 2rem;
          }

          section[data-testid="stSidebar"] {
            background: #f8fafc;
            border-right: 1px solid var(--border);
          }

          .app-header {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 16px 20px;
            box-shadow: var(--shadow);
            margin-bottom: 16px;
          }

          .app-title {
            color: var(--text);
            font-size: 1.6rem;
            font-weight: 700;
            margin: 0;
            line-height: 1.2;
          }

          .app-subtitle {
            color: var(--text-soft);
            margin-top: 6px;
            margin-bottom: 0;
            font-size: 0.96rem;
          }

          .freshness-pill {
            display: inline-block;
            margin-top: 10px;
            padding: 4px 10px;
            border-radius: 999px;
            border: 1px solid #bdece8;
            background: #ecfbf9;
            color: #0a5b55;
            font-weight: 600;
            font-size: 0.85rem;
          }

          .filter-context {
            margin-top: 12px;
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
          }

          .filter-chip {
            display: inline-block;
            padding: 3px 9px;
            border-radius: 999px;
            border: 1px solid var(--border);
            background: #ffffff;
            color: var(--text-secondary);
            font-size: 0.8rem;
            font-weight: 500;
          }

          .kpi-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 14px;
            box-shadow: var(--shadow);
            min-height: 154px;
            margin-bottom: 12px;
          }

          .kpi-id {
            color: var(--accent);
            font-weight: 700;
            letter-spacing: 0.02em;
            font-size: 0.84rem;
            margin-bottom: 2px;
          }

          .kpi-name {
            color: var(--text);
            font-size: 0.95rem;
            font-weight: 600;
            line-height: 1.2;
          }

          .kpi-value {
            color: var(--text);
            font-size: 1.5rem;
            font-weight: 700;
            margin: 8px 0;
          }

          .kpi-detail {
            color: var(--text-soft);
            font-size: 0.82rem;
          }

          .section-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 16px;
            box-shadow: var(--shadow);
            margin-bottom: 14px;
          }

          .section-heading-wrap {
            margin-top: 16px;
            margin-bottom: 8px;
          }

          .section-title {
            color: var(--text-secondary);
            font-size: 1.03rem;
            font-weight: 700;
            margin: 0;
            padding: 8px 12px;
            border-left: 4px solid var(--accent);
            border-radius: 8px;
            background: #f9fcfb;
            border-top: 1px solid var(--border);
            border-right: 1px solid var(--border);
            border-bottom: 1px solid var(--border);
          }

          div[data-testid="stPlotlyChart"],
          div[data-testid="stDataFrame"],
          div[data-testid="stTable"],
          div[data-testid="stMetric"],
          div.stDownloadButton,
          div[data-testid="stAlert"] {
            margin-top: 6px;
            margin-bottom: 14px;
          }

          @media (max-width: 992px) {
            .app-title { font-size: 1.35rem; }
            .kpi-card { min-height: 138px; }
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _join_values(items: Iterable[str], limit: int = 3) -> str:
    values = list(items)
    if not values:
        return "All"
    if len(values) <= limit:
        return ", ".join(values)
    return f"{', '.join(values[:limit])} +{len(values) - limit} more"


def render_header(title: str, subtitle: str, fetched_at_utc, filters: FilterContext | None = None) -> None:
    last_refresh = fetched_at_utc.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    ttl_minutes = CACHE_TTL_SECONDS // 60
    filter_html = ""
    if filters is not None:
        chips = [
            f"<span class='filter-chip'>Date: {filters.start_date} to {filters.end_date}</span>"
            if filters.start_date and filters.end_date
            else "<span class='filter-chip'>Date: All</span>",
            f"<span class='filter-chip'>State: {_join_values(filters.states)}</span>",
            f"<span class='filter-chip'>City: {_join_values(filters.cities)}</span>",
            f"<span class='filter-chip'>Manufacturer: {_join_values(filters.manufacturers)}</span>",
            f"<span class='filter-chip'>Model: {_join_values(filters.models)}</span>",
            f"<span class='filter-chip'>Activity: {_join_values(filters.activities)}</span>",
        ]
        filter_html = f"<div class='filter-context'>{''.join(chips)}</div>"

    st.markdown(
        f"""
        <div class="app-header">
          <h1 class="app-title">{title}</h1>
          <p class="app-subtitle">{subtitle}</p>
          <div class="freshness-pill">Live from Target Neon DB | Last refresh (UTC): {last_refresh} | Cache TTL: {ttl_minutes} minutes</div>
          {filter_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_info(name: str) -> None:
    st.markdown(
        f"""
        <div class="section-card">
          <strong>{name}</strong>: no data available for selected filters.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_error_info(name: str, message: str) -> None:
    st.error(f"{name}: {message}")


def render_section_heading(title: str) -> None:
    st.markdown(
        f"""
        <div class="section-heading-wrap">
          <div class="section-title">{title}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_chart_style(fig: go.Figure, height: int = 460, show_legend: bool = False) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor=PALETTE["card"],
        plot_bgcolor=PALETTE["card"],
        font=dict(family="Inter, sans-serif", color=PALETTE["secondary"], size=13),
        showlegend=show_legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=PALETTE["border"], font_size=12),
    )
    fig.update_xaxes(gridcolor="#edf2f7", zeroline=False, linecolor=PALETTE["border"])
    fig.update_yaxes(gridcolor="#edf2f7", zeroline=False, linecolor=PALETTE["border"])
    return fig


def format_kpi(row: dict) -> str:
  def format_inr_compact(value: float) -> str:
    sign = "-" if value < 0 else ""
    amount = abs(float(value))
    if amount >= 10_000_000:
      return f"{sign}INR {amount / 10_000_000:.2f} Cr"
    if amount >= 100_000:
      return f"{sign}INR {amount / 100_000:.2f} L"
    if amount >= 1_000:
      return f"{sign}INR {amount / 1_000:.2f} K"
    return f"{sign}INR {amount:.2f}"

  kpi_id = row["kpi_id"]
  value = row["value"]
  if kpi_id == "KPI1":
    return f"{int(value):,}"
  if kpi_id in {"KPI2", "KPI3"}:
    return format_inr_compact(float(value))
  if kpi_id in {"KPI4", "KPI5"}:
    return f"{float(value):,.2f}%"
  return str(value)


def render_kpi_cards(kpi_df: pd.DataFrame) -> None:
    cards = st.columns(5)
    for idx, row in kpi_df.iterrows():
        with cards[idx % 5]:
            st.markdown(
                f"""
                <div class="kpi-card">
                  <div class="kpi-id">{row['kpi_id']}</div>
                  <div class="kpi-name">{row['kpi_name']}</div>
                  <div class="kpi-value">{format_kpi(row)}</div>
                  <div class="kpi-detail">{row['detail']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_filter_sidebar() -> FilterContext:
  st.sidebar.header("Global Filters")
  st.sidebar.caption("Leave a filter empty to include all values.")

  min_date, max_date = get_data_date_range()
  if min_date is None or max_date is None:
    filters = FilterContext()
    st.session_state["ev_filters"] = filters
    return filters

  if st.sidebar.button("Clear filters", width="stretch"):
    st.session_state["ev_start_date"] = min_date
    st.session_state["ev_end_date"] = max_date
    st.session_state["ev_date_range"] = (min_date, max_date)
    st.session_state["ev_state"] = []
    st.session_state["ev_city"] = []
    st.session_state["ev_manu"] = []
    st.session_state["ev_model"] = []
    st.session_state["ev_activity"] = []
    st.session_state["ev_filters"] = FilterContext(start_date=min_date, end_date=max_date)
    st.rerun()

  default_start = st.session_state.get("ev_start_date", min_date)
  default_end = st.session_state.get("ev_end_date", max_date)
  if "ev_date_range" not in st.session_state:
    st.session_state["ev_date_range"] = (default_start, default_end)
  else:
    existing_dates = st.session_state.get("ev_date_range")
    if isinstance(existing_dates, tuple) and len(existing_dates) == 2:
      existing_start = min(max(existing_dates[0], min_date), max_date)
      existing_end = min(max(existing_dates[1], min_date), max_date)
      if existing_start > existing_end:
        existing_start, existing_end = min_date, max_date
      st.session_state["ev_date_range"] = (existing_start, existing_end)
    else:
      st.session_state["ev_date_range"] = (default_start, default_end)

  selected_dates = st.sidebar.date_input(
    "Date range",
    min_value=min_date,
    max_value=max_date,
    key="ev_date_range",
  )

  if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
  else:
    start_date, end_date = min_date, max_date

  st.session_state["ev_start_date"] = start_date
  st.session_state["ev_end_date"] = end_date

  base = FilterContext(start_date=start_date, end_date=end_date)
  state_options = get_dimension_options(base, "state")
  if "ev_state" not in st.session_state:
    st.session_state["ev_state"] = []
  else:
    st.session_state["ev_state"] = [x for x in st.session_state.get("ev_state", []) if x in state_options]
  selected_states = st.sidebar.multiselect(
    "State",
    options=state_options,
    key="ev_state",
  )

  city_ctx = FilterContext(start_date=start_date, end_date=end_date, states=tuple(selected_states))
  city_options = get_dimension_options(city_ctx, "city")
  if "ev_city" not in st.session_state:
    st.session_state["ev_city"] = []
  else:
    st.session_state["ev_city"] = [x for x in st.session_state.get("ev_city", []) if x in city_options]
  selected_cities = st.sidebar.multiselect(
    "City",
    options=city_options,
    key="ev_city",
  )

  manu_ctx = FilterContext(
    start_date=start_date,
    end_date=end_date,
    states=tuple(selected_states),
    cities=tuple(selected_cities),
  )
  manu_options = get_dimension_options(manu_ctx, "manufacturer")
  if "ev_manu" not in st.session_state:
    st.session_state["ev_manu"] = []
  else:
    st.session_state["ev_manu"] = [x for x in st.session_state.get("ev_manu", []) if x in manu_options]
  selected_manu = st.sidebar.multiselect(
    "Manufacturer",
    options=manu_options,
    key="ev_manu",
  )

  model_ctx = FilterContext(
    start_date=start_date,
    end_date=end_date,
    states=tuple(selected_states),
    cities=tuple(selected_cities),
    manufacturers=tuple(selected_manu),
  )
  model_options = get_dimension_options(model_ctx, "model")
  if "ev_model" not in st.session_state:
    st.session_state["ev_model"] = []
  else:
    st.session_state["ev_model"] = [x for x in st.session_state.get("ev_model", []) if x in model_options]
  selected_models = st.sidebar.multiselect(
    "EV model",
    options=model_options,
    key="ev_model",
  )

  activity_ctx = FilterContext(
    start_date=start_date,
    end_date=end_date,
    states=tuple(selected_states),
    cities=tuple(selected_cities),
    manufacturers=tuple(selected_manu),
    models=tuple(selected_models),
  )
  activity_options = get_dimension_options(activity_ctx, "activity")
  if "ev_activity" not in st.session_state:
    st.session_state["ev_activity"] = []
  else:
    st.session_state["ev_activity"] = [x for x in st.session_state.get("ev_activity", []) if x in activity_options]
  selected_activities = st.sidebar.multiselect(
    "Activity type",
    options=activity_options,
    key="ev_activity",
  )

  if st.sidebar.button("Refresh data now", width="stretch"):
    st.cache_data.clear()
    st.rerun()

  filters = FilterContext(
    start_date=start_date,
    end_date=end_date,
    states=tuple(selected_states),
    cities=tuple(selected_cities),
    manufacturers=tuple(selected_manu),
    models=tuple(selected_models),
    activities=tuple(selected_activities),
  )
  st.session_state["ev_filters"] = filters
  return filters


def get_active_filters() -> FilterContext:
  stored = st.session_state.get("ev_filters")
  if isinstance(stored, FilterContext):
    return stored

  return FilterContext(
    start_date=st.session_state.get("ev_start_date"),
    end_date=st.session_state.get("ev_end_date"),
    states=tuple(st.session_state.get("ev_state", [])),
    cities=tuple(st.session_state.get("ev_city", [])),
    manufacturers=tuple(st.session_state.get("ev_manu", [])),
    models=tuple(st.session_state.get("ev_model", [])),
    activities=tuple(st.session_state.get("ev_activity", [])),
  )
