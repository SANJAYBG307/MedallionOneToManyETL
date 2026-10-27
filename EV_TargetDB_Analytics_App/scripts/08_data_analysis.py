from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import CSV_DIR, ensure_reports, prepared_path


def compute_kpis(prepared: pd.DataFrame) -> pd.DataFrame:
    # Compute KPI1 to KPI5.
    total_txn = int(prepared["transaction_id"].nunique())
    total_revenue = float(prepared["revenue_amount"].sum())

    sale = prepared[prepared["activity_type"] == "Sale"]
    sale_txn = int(sale["transaction_id"].nunique())
    sale_total_price = float(sale["final_price"].sum())
    asp_sale = float(sale_total_price / sale_txn) if sale_txn else 0.0

    warranty_txn = int(prepared.loc[prepared["warranty_claim_flag"] == True, "transaction_id"].nunique())
    warranty_rate = float((warranty_txn / total_txn) * 100) if total_txn else 0.0

    rows = [
        {"kpi_id": "KPI1", "kpi_name": "Total EV Transactions", "value": total_txn},
        {"kpi_id": "KPI2", "kpi_name": "Total EV Revenue", "value": total_revenue},
        {"kpi_id": "KPI3", "kpi_name": "Average Selling Price per Transaction (Sale)", "value": asp_sale},
        {"kpi_id": "KPI4", "kpi_name": "Manufacturer Market Share (%)", "value": 100.0},
        {"kpi_id": "KPI5", "kpi_name": "Warranty Claim Rate (%)", "value": warranty_rate},
    ]
    return pd.DataFrame(rows)


def bq1_transaction_trend(prepared: pd.DataFrame) -> pd.DataFrame:
    return (
        prepared.groupby(["year_num", "month_num", "month_name"], dropna=False)["transaction_id"]
        .nunique()
        .reset_index(name="total_transactions")
        .sort_values(["year_num", "month_num"])
    )


def bq2_geography(prepared: pd.DataFrame) -> pd.DataFrame:
    return (
        prepared.groupby(["state", "city"], dropna=False)["transaction_id"]
        .nunique()
        .reset_index(name="total_transactions")
        .sort_values("total_transactions", ascending=False)
    )


def bq3_manufacturer_revenue(prepared: pd.DataFrame) -> pd.DataFrame:
    out = (
        prepared.groupby("manufacturer_name", dropna=False)["revenue_amount"]
        .sum()
        .reset_index(name="manufacturer_revenue")
        .sort_values("manufacturer_revenue", ascending=False)
    )
    total = float(out["manufacturer_revenue"].sum())
    out["market_share_pct"] = (out["manufacturer_revenue"] / total * 100) if total else 0.0
    return out


def bq4_model_popularity(prepared: pd.DataFrame) -> pd.DataFrame:
    return (
        prepared.groupby("model_name", dropna=False)["transaction_id"]
        .nunique()
        .reset_index(name="total_transactions")
        .sort_values("total_transactions", ascending=False)
    )


def bq5_activity_share(prepared: pd.DataFrame) -> pd.DataFrame:
    out = (
        prepared.groupby("activity_type", dropna=False)["transaction_id"]
        .nunique()
        .reset_index(name="total_transactions")
        .sort_values("total_transactions", ascending=False)
    )
    total = float(out["total_transactions"].sum())
    out["activity_share_pct"] = (out["total_transactions"] / total * 100) if total else 0.0
    return out


def build_bq_outputs(prepared: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {
        "BQ1": bq1_transaction_trend(prepared),
        "BQ2": bq2_geography(prepared),
        "BQ3": bq3_manufacturer_revenue(prepared),
        "BQ4": bq4_model_popularity(prepared),
        "BQ5": bq5_activity_share(prepared),
    }


def main() -> None:
    # Build KPI and BQ outputs.
    prepared = pd.read_csv(prepared_path())

    kpis = compute_kpis(prepared)
    bqs = build_bq_outputs(prepared)

    ensure_reports()
    kpis.to_csv(CSV_DIR / "08_kpis.csv", index=False)
    for name, frame in bqs.items():
        frame.to_csv(CSV_DIR / f"08_{name}.csv", index=False)

    print("Stage 08 complete: Data Analysis")
    print("  - reports/csv/08_kpis.csv")
    print("  - reports/csv/08_BQ1..BQ5.csv")


if __name__ == "__main__":
    main()
