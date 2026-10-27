from __future__ import annotations

from pathlib import Path
import sys
from typing import Dict

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import TABLE_NAMES, CSV_DIR, ensure_reports, raw_table_path


def profile_tables(tables: Dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    # Basic table profile.
    rows: list[dict[str, object]] = []
    for name, df in tables.items():
        rows.append(
            {
                "table": name,
                "row_count": int(len(df)),
                "column_count": int(df.shape[1]),
                "null_cells": int(df.isna().sum().sum()),
            }
        )

    # Activity frequency profile.
    activity_df = tables["dim_activity"].copy()
    activity_summary = (
        activity_df["activity_type"]
        .fillna("<NULL>")
        .value_counts(dropna=False)
        .rename_axis("activity_type")
        .reset_index(name="count")
        .sort_values("activity_type")
    )

    return pd.DataFrame(rows), activity_summary


def main() -> None:
    # Profile raw tables.
    tables: Dict[str, pd.DataFrame] = {}
    for table_name in TABLE_NAMES:
        tables[table_name] = pd.read_csv(raw_table_path(table_name))

    profile_summary, activity_summary = profile_tables(tables)

    ensure_reports()
    profile_summary.to_csv(CSV_DIR / "02_profile_summary.csv", index=False)
    activity_summary.to_csv(CSV_DIR / "02_activity_summary.csv", index=False)

    print("Stage 02 complete: Data Profiling")
    print("  - reports/csv/02_profile_summary.csv")
    print("  - reports/csv/02_activity_summary.csv")


if __name__ == "__main__":
    main()
