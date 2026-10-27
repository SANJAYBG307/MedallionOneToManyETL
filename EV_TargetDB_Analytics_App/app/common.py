from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
import re
import sys
from typing import Any

import pandas as pd
import streamlit as st
from sqlalchemy import bindparam, text
from sqlalchemy.engine import Engine

CACHE_TTL_SECONDS = 1800

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.config import load_settings
from scripts.db import get_engine


@dataclass(frozen=True)
class FilterContext:
    start_date: date | None = None
    end_date: date | None = None
    states: tuple[str, ...] = ()
    cities: tuple[str, ...] = ()
    manufacturers: tuple[str, ...] = ()
    models: tuple[str, ...] = ()
    activities: tuple[str, ...] = ()


def _safe_identifier(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ValueError("Unsafe identifier provided")
    return name


def _schema() -> str:
    return _safe_identifier(load_settings().target_schema)


@st.cache_resource(show_spinner=False)
def get_db_engine() -> Engine:
    return get_engine()


def _base_from_clause(schema: str, required_dims: set[str] | None = None) -> str:
    required_dims = required_dims or set()
    joins: list[str] = [f'FROM "{schema}"."fact_ev_activity" f']

    if "date" in required_dims:
        joins.append(f'LEFT JOIN "{schema}"."dim_date" d ON f.date_key = d.date_key')
    if "location" in required_dims:
        joins.append(f'LEFT JOIN "{schema}"."dim_location" l ON f.location_key = l.location_key')
    if "manufacturer" in required_dims:
        joins.append(f'LEFT JOIN "{schema}"."dim_manufacturer" m ON f.manufacturer_key = m.manufacturer_key')
    if "vehicle" in required_dims:
        joins.append(f'LEFT JOIN "{schema}"."dim_vehicle" v ON f.vehicle_key = v.vehicle_key')
    if "activity" in required_dims:
        joins.append(f'LEFT JOIN "{schema}"."dim_activity" a ON f.activity_key = a.activity_key')

    return "\n    " + "\n    ".join(joins)


def _required_dims_for_filters(filters: FilterContext, exclude: set[str] | None = None) -> set[str]:
    exclude = exclude or set()
    dims: set[str] = set()

    if (
        (filters.start_date and "start_date" not in exclude)
        or (filters.end_date and "end_date" not in exclude)
    ):
        dims.add("date")
    if (
        (filters.states and "states" not in exclude)
        or (filters.cities and "cities" not in exclude)
    ):
        dims.add("location")
    if filters.manufacturers and "manufacturers" not in exclude:
        dims.add("manufacturer")
    if filters.models and "models" not in exclude:
        dims.add("vehicle")
    if filters.activities and "activities" not in exclude:
        dims.add("activity")

    return dims


def _build_where_clause(filters: FilterContext, exclude: set[str] | None = None) -> tuple[str, dict[str, Any], set[str]]:
    exclude = exclude or set()
    conditions: list[str] = ["f.transaction_id IS NOT NULL"]
    params: dict[str, Any] = {}
    expanding: set[str] = set()

    if filters.start_date and "start_date" not in exclude:
        conditions.append("d.full_date >= :start_date")
        params["start_date"] = filters.start_date
    if filters.end_date and "end_date" not in exclude:
        conditions.append("d.full_date <= :end_date")
        params["end_date"] = filters.end_date

    if filters.states and "states" not in exclude:
        conditions.append("l.state IN :states")
        params["states"] = list(filters.states)
        expanding.add("states")
    if filters.cities and "cities" not in exclude:
        conditions.append("l.city IN :cities")
        params["cities"] = list(filters.cities)
        expanding.add("cities")
    if filters.manufacturers and "manufacturers" not in exclude:
        conditions.append("m.manufacturer_name IN :manufacturers")
        params["manufacturers"] = list(filters.manufacturers)
        expanding.add("manufacturers")
    if filters.models and "models" not in exclude:
        conditions.append("v.model_name IN :models")
        params["models"] = list(filters.models)
        expanding.add("models")
    if filters.activities and "activities" not in exclude:
        conditions.append("a.activity_type IN :activities")
        params["activities"] = list(filters.activities)
        expanding.add("activities")

    return " WHERE " + " AND ".join(conditions), params, expanding


def _read_sql(sql: str, params: dict[str, Any], expanding: set[str]) -> pd.DataFrame:
    try:
        stmt = text(sql)
        for key in sorted(expanding):
            stmt = stmt.bindparams(bindparam(key, expanding=True))
        return pd.read_sql_query(stmt, get_db_engine(), params=params)
    except Exception as exc:
        raise RuntimeError("Database query failed. Please verify filters or database availability.") from exc


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_data_date_range() -> tuple[date | None, date | None]:
    schema = _schema()
    from_clause = _base_from_clause(schema, required_dims={"date"})
    sql = f'''
    SELECT
        MIN(d.full_date)::date AS min_date,
        MAX(d.full_date)::date AS max_date
    {from_clause}
    WHERE f.transaction_id IS NOT NULL
    '''
    frame = _read_sql(sql, params={}, expanding=set())
    if frame.empty or frame.loc[0, "min_date"] is None or frame.loc[0, "max_date"] is None:
        return None, None
    return pd.to_datetime(frame.loc[0, "min_date"]).date(), pd.to_datetime(frame.loc[0, "max_date"]).date()


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_dimension_options(filters: FilterContext, dimension: str) -> list[str]:
    schema = _schema()
    mapping = {
        "state": ("states", "l.state"),
        "city": ("cities", "l.city"),
        "manufacturer": ("manufacturers", "m.manufacturer_name"),
        "model": ("models", "v.model_name"),
        "activity": ("activities", "a.activity_type"),
    }
    if dimension not in mapping:
        return []

    exclude_key, column_expr = mapping[dimension]
    where_sql, params, expanding = _build_where_clause(filters, exclude={exclude_key})
    required_dims = _required_dims_for_filters(filters, exclude={exclude_key})
    if dimension in {"state", "city"}:
        required_dims.add("location")
    elif dimension == "manufacturer":
        required_dims.add("manufacturer")
    elif dimension == "model":
        required_dims.add("vehicle")
    elif dimension == "activity":
        required_dims.add("activity")

    from_clause = _base_from_clause(schema, required_dims=required_dims)
    sql = f'''
    SELECT DISTINCT {column_expr} AS value
    {from_clause}
    {where_sql}
      AND {column_expr} IS NOT NULL
      AND BTRIM({column_expr}::text) <> ''
    ORDER BY value
    '''
    frame = _read_sql(sql, params=params, expanding=expanding)
    if frame.empty:
        return []
    return [str(v) for v in frame["value"].dropna().tolist()]


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_kpis(filters: FilterContext) -> pd.DataFrame:
    schema = _schema()
    where_sql, params, expanding = _build_where_clause(filters)
    required_dims = _required_dims_for_filters(filters) | {"activity", "manufacturer"}
    from_clause = _base_from_clause(schema, required_dims=required_dims)
    sql = f'''
    WITH filtered AS (
        SELECT DISTINCT
            f.transaction_id,
            COALESCE(f.revenue_amount, 0) AS revenue_amount,
            COALESCE(f.final_price, 0) AS final_price,
            f.warranty_claim_flag,
            a.activity_type,
            m.manufacturer_name
        {from_clause}
        {where_sql}
    ),
    totals AS (
        SELECT
            COUNT(DISTINCT transaction_id) AS total_transactions,
            SUM(revenue_amount) AS total_revenue,
            COUNT(DISTINCT CASE WHEN activity_type = 'Sale' THEN transaction_id END) AS sale_transactions,
            SUM(CASE WHEN activity_type = 'Sale' THEN final_price ELSE 0 END) AS sale_total_price,
            COUNT(DISTINCT CASE WHEN warranty_claim_flag IS TRUE THEN transaction_id END) AS claimed_transactions
        FROM filtered
    ),
    top_manufacturer AS (
        SELECT
            manufacturer_name,
            SUM(revenue_amount) AS manufacturer_revenue
        FROM filtered
        GROUP BY manufacturer_name
        ORDER BY manufacturer_revenue DESC NULLS LAST
        LIMIT 1
    )
    SELECT
        t.total_transactions,
        t.total_revenue,
        CASE
            WHEN t.sale_transactions > 0 THEN t.sale_total_price / t.sale_transactions
            ELSE 0
        END AS avg_selling_price,
        CASE
            WHEN t.total_revenue > 0 THEN COALESCE(tm.manufacturer_revenue, 0) / t.total_revenue * 100
            ELSE 0
        END AS top_manufacturer_market_share_pct,
        COALESCE(tm.manufacturer_name, 'N/A') AS top_manufacturer_name,
        CASE
            WHEN t.total_transactions > 0 THEN t.claimed_transactions::numeric / t.total_transactions * 100
            ELSE 0
        END AS warranty_claim_rate
    FROM totals t
    LEFT JOIN top_manufacturer tm ON TRUE
    '''
    frame = _read_sql(sql, params=params, expanding=expanding)
    if frame.empty:
        return pd.DataFrame(
            [
                {"kpi_id": "KPI1", "kpi_name": "Total EV Transactions", "value": 0, "detail": "Distinct transactions"},
                {"kpi_id": "KPI2", "kpi_name": "Total EV Revenue", "value": 0.0, "detail": "Sum of revenue_amount"},
                {
                    "kpi_id": "KPI3",
                    "kpi_name": "Average Selling Price per Transaction",
                    "value": 0.0,
                    "detail": "Sale final_price / distinct Sale transactions",
                },
                {
                    "kpi_id": "KPI4",
                    "kpi_name": "Manufacturer Market Share",
                    "value": 0.0,
                    "detail": "Top manufacturer revenue share",
                },
                {
                    "kpi_id": "KPI5",
                    "kpi_name": "Warranty Claim Rate",
                    "value": 0.0,
                    "detail": "Distinct claimed / distinct transactions",
                },
            ]
        )

    row = frame.iloc[0]
    return pd.DataFrame(
        [
            {
                "kpi_id": "KPI1",
                "kpi_name": "Total EV Transactions",
                "value": int(row["total_transactions"] or 0),
                "detail": "Distinct transactions",
            },
            {
                "kpi_id": "KPI2",
                "kpi_name": "Total EV Revenue",
                "value": float(row["total_revenue"] or 0),
                "detail": "Sum of revenue_amount",
            },
            {
                "kpi_id": "KPI3",
                "kpi_name": "Average Selling Price per Transaction",
                "value": float(row["avg_selling_price"] or 0),
                "detail": "Sale final_price / distinct Sale transactions",
            },
            {
                "kpi_id": "KPI4",
                "kpi_name": "Manufacturer Market Share",
                "value": float(row["top_manufacturer_market_share_pct"] or 0),
                "detail": f"Top manufacturer: {row['top_manufacturer_name']}",
            },
            {
                "kpi_id": "KPI5",
                "kpi_name": "Warranty Claim Rate",
                "value": float(row["warranty_claim_rate"] or 0),
                "detail": "Distinct claimed / distinct transactions",
            },
        ]
    )


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_bq1_trend(filters: FilterContext) -> pd.DataFrame:
    schema = _schema()
    where_sql, params, expanding = _build_where_clause(filters)
    required_dims = _required_dims_for_filters(filters) | {"date"}
    from_clause = _base_from_clause(schema, required_dims=required_dims)
    sql = f'''
    SELECT
        d.year_num,
        d.month_num,
        d.month_name,
        DATE_TRUNC('month', d.full_date)::date AS month_start,
        COUNT(DISTINCT f.transaction_id) AS total_transactions
    {from_clause}
    {where_sql}
    GROUP BY d.year_num, d.month_num, d.month_name, DATE_TRUNC('month', d.full_date)
    ORDER BY month_start
    '''
    return _read_sql(sql, params=params, expanding=expanding)


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_bq1_trend_by_grain(filters: FilterContext, grain: str = "month") -> pd.DataFrame:
    schema = _schema()
    where_sql, params, expanding = _build_where_clause(filters)
    required_dims = _required_dims_for_filters(filters) | {"date"}
    from_clause = _base_from_clause(schema, required_dims=required_dims)

    if grain == "day":
        select_expr = "d.full_date::date"
        alias = "period_start"
    elif grain == "year":
        select_expr = "DATE_TRUNC('year', d.full_date)::date"
        alias = "period_start"
    else:
        select_expr = "DATE_TRUNC('month', d.full_date)::date"
        alias = "period_start"

    sql = f'''
    SELECT
        {select_expr} AS {alias},
        COUNT(DISTINCT f.transaction_id) AS total_transactions
    {from_clause}
    {where_sql}
    GROUP BY {select_expr}
    ORDER BY {alias}
    '''
    return _read_sql(sql, params=params, expanding=expanding)


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_bq2_geography(filters: FilterContext) -> pd.DataFrame:
    schema = _schema()
    where_sql, params, expanding = _build_where_clause(filters)
    required_dims = _required_dims_for_filters(filters) | {"location"}
    from_clause = _base_from_clause(schema, required_dims=required_dims)
    sql = f'''
    SELECT
        COALESCE(l.state, 'Unknown') AS state,
        COALESCE(l.city, 'Unknown') AS city,
        COUNT(DISTINCT f.transaction_id) AS total_transactions
    {from_clause}
    {where_sql}
    GROUP BY COALESCE(l.state, 'Unknown'), COALESCE(l.city, 'Unknown')
    ORDER BY total_transactions DESC
    '''
    return _read_sql(sql, params=params, expanding=expanding)


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_bq3_manufacturer(filters: FilterContext) -> pd.DataFrame:
    schema = _schema()
    where_sql, params, expanding = _build_where_clause(filters)
    required_dims = _required_dims_for_filters(filters) | {"manufacturer"}
    from_clause = _base_from_clause(schema, required_dims=required_dims)
    sql = f'''
    WITH grouped AS (
        SELECT
            COALESCE(m.manufacturer_name, 'Unknown') AS manufacturer_name,
            SUM(COALESCE(f.revenue_amount, 0)) AS manufacturer_revenue
        {from_clause}
        {where_sql}
        GROUP BY COALESCE(m.manufacturer_name, 'Unknown')
    )
    SELECT
        manufacturer_name,
        manufacturer_revenue,
        CASE
            WHEN SUM(manufacturer_revenue) OVER () > 0
                THEN manufacturer_revenue / SUM(manufacturer_revenue) OVER () * 100
            ELSE 0
        END AS market_share_pct
    FROM grouped
    ORDER BY manufacturer_revenue DESC
    '''
    return _read_sql(sql, params=params, expanding=expanding)


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_bq4_models(filters: FilterContext) -> pd.DataFrame:
    schema = _schema()
    where_sql, params, expanding = _build_where_clause(filters)
    required_dims = _required_dims_for_filters(filters) | {"vehicle"}
    from_clause = _base_from_clause(schema, required_dims=required_dims)
    sql = f'''
    SELECT
        COALESCE(v.model_name, 'Unknown') AS model_name,
        COUNT(DISTINCT f.transaction_id) AS total_transactions
    {from_clause}
    {where_sql}
    GROUP BY COALESCE(v.model_name, 'Unknown')
    ORDER BY total_transactions DESC
    '''
    return _read_sql(sql, params=params, expanding=expanding)


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_bq5_activity_share(filters: FilterContext) -> pd.DataFrame:
    schema = _schema()
    where_sql, params, expanding = _build_where_clause(filters)
    required_dims = _required_dims_for_filters(filters) | {"activity"}
    from_clause = _base_from_clause(schema, required_dims=required_dims)
    sql = f'''
    WITH grouped AS (
        SELECT
            COALESCE(a.activity_type, 'Unknown') AS activity_type,
            COUNT(DISTINCT f.transaction_id) AS total_transactions
        {from_clause}
        {where_sql}
        GROUP BY COALESCE(a.activity_type, 'Unknown')
    ),
    total AS (
        SELECT COUNT(DISTINCT f.transaction_id) AS total_distinct_transactions
        {from_clause}
        {where_sql}
    )
    SELECT
        g.activity_type,
        g.total_transactions,
        CASE
            WHEN t.total_distinct_transactions > 0
                THEN g.total_transactions::numeric / t.total_distinct_transactions * 100
            ELSE 0
        END AS activity_share_pct
    FROM grouped g
    CROSS JOIN total t
    ORDER BY g.total_transactions DESC
    '''
    return _read_sql(sql, params=params, expanding=expanding)


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_detail_rows(filters: FilterContext, limit: int = 5000) -> pd.DataFrame:
    schema = _schema()
    where_sql, params, expanding = _build_where_clause(filters)
    required_dims = _required_dims_for_filters(filters) | {
        "date",
        "location",
        "manufacturer",
        "vehicle",
        "activity",
    }
    from_clause = _base_from_clause(schema, required_dims=required_dims)
    params = {**params, "row_limit": int(limit)}
    sql = f'''
    SELECT DISTINCT
        f.transaction_id,
        d.full_date,
        COALESCE(l.state, 'Unknown') AS state,
        COALESCE(l.city, 'Unknown') AS city,
        COALESCE(m.manufacturer_name, 'Unknown') AS manufacturer_name,
        COALESCE(v.model_name, 'Unknown') AS model_name,
        COALESCE(a.activity_type, 'Unknown') AS activity_type,
        COALESCE(f.revenue_amount, 0) AS revenue_amount,
        COALESCE(f.final_price, 0) AS final_price,
        f.warranty_claim_flag
    {from_clause}
    {where_sql}
    ORDER BY d.full_date DESC NULLS LAST
    LIMIT :row_limit
    '''
    return _read_sql(sql, params=params, expanding=expanding)


def get_dashboard_payload(filters: FilterContext) -> dict[str, Any]:
    return {
        "kpis": get_kpis(filters),
        "bq1": get_bq1_trend(filters),
        "bq2": get_bq2_geography(filters),
        "bq3": get_bq3_manufacturer(filters),
        "bq4": get_bq4_models(filters),
        "bq5": get_bq5_activity_share(filters),
        "detail": get_detail_rows(filters),
        "fetched_at_utc": datetime.now(timezone.utc),
    }


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_freshness_timestamp_utc() -> datetime:
    return datetime.now(timezone.utc)


def get_artifacts() -> dict[str, Any]:
    # Compatibility helper for existing page files.
    payload = get_dashboard_payload(FilterContext())
    return {
        "model": payload["detail"],
        "dq": pd.DataFrame(),
        "profile_summary": pd.DataFrame(),
        "activity_summary": pd.DataFrame(),
        "eda_outputs": {
            "numeric_summary": pd.DataFrame(),
            "activity_mix": pd.DataFrame(),
            "top_states": pd.DataFrame(),
        },
        "kpis": payload["kpis"],
        "bqs": {
            "BQ1": payload["bq1"],
            "BQ2": payload["bq2"],
            "BQ3": payload["bq3"],
            "BQ4": payload["bq4"],
            "BQ5": payload["bq5"],
        },
    }
