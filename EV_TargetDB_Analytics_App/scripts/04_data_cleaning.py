from __future__ import annotations

from pathlib import Path
import sys
from typing import Dict

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import TABLE_NAMES, ensure_reports, raw_table_path, clean_table_path


TEXT_COLUMNS = {
    "dim_location": ["state", "city"],
    "dim_manufacturer": ["manufacturer_name"],
    "dim_vehicle": ["model_name"],
    "dim_activity": ["activity_type"],
}


def clean_tables(tables: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    # Clean and standardize key fields.
    cleaned: Dict[str, pd.DataFrame] = {k: v.copy() for k, v in tables.items()}

    fact = cleaned["fact_ev_activity"]
    fact["revenue_amount"] = pd.to_numeric(fact["revenue_amount"], errors="coerce")
    fact["final_price"] = pd.to_numeric(fact["final_price"], errors="coerce")
    if "event_date" in fact.columns:
        fact["event_date"] = pd.to_datetime(fact["event_date"], errors="coerce")

    for table_name, cols in TEXT_COLUMNS.items():
        frame = cleaned[table_name]
        for col in cols:
            frame[col] = frame[col].astype("string").str.strip()

    return cleaned


def main() -> None:
    # Clean data for safe analysis.
    tables: Dict[str, pd.DataFrame] = {}
    for table_name in TABLE_NAMES:
        tables[table_name] = pd.read_csv(raw_table_path(table_name))

    cleaned = clean_tables(tables)

    ensure_reports()
    for table_name, frame in cleaned.items():
        frame.to_csv(clean_table_path(table_name), index=False)

    print("Stage 04 complete: Data Cleaning")


if __name__ == "__main__":
    main()
