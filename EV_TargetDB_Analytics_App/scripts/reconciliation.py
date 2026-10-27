from __future__ import annotations

import pandas as pd


def reconcile_outputs(
    model: pd.DataFrame,
    bq_outputs: dict[str, pd.DataFrame],
    kpis: pd.DataFrame,
) -> pd.DataFrame:
    kpi1 = int(kpis.loc[kpis["kpi_id"] == "KPI1", "value"].iloc[0])

    bq1_total = int(bq_outputs["BQ1"]["total_transactions"].sum())
    bq5_total = int(bq_outputs["BQ5"]["total_transactions"].sum())

    checks = [
        {
            "check_name": "KPI1_vs_BQ1_sum",
            "passed": kpi1 == bq1_total,
            "left_value": kpi1,
            "right_value": bq1_total,
        },
        {
            "check_name": "KPI1_vs_BQ5_sum",
            "passed": kpi1 == bq5_total,
            "left_value": kpi1,
            "right_value": bq5_total,
        },
        {
            "check_name": "model_row_count_positive",
            "passed": len(model) > 0,
            "left_value": len(model),
            "right_value": 1,
        },
    ]

    return pd.DataFrame(checks)
