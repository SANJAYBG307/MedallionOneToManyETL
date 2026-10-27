from __future__ import annotations

from pathlib import Path
import sys
from typing import Dict

import pandas as pd
from sqlalchemy.engine import Engine

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import load_settings
from db import get_engine
from scripts._common import ensure_reports, raw_table_path


# Required columns for project scope.
REQUIRED_COLUMNS: dict[str, list[str]] = {
    "fact_ev_activity": [
        "transaction_id",
        "event_date",
        "date_key",
        "location_key",
        "manufacturer_key",
        "vehicle_key",
        "activity_key",
        "revenue_amount",
        "final_price",
        "warranty_claim_flag",
    ],
    "dim_date": [
        "date_key",
        "full_date",
        "month_num",
        "month_name",
        "quarter_num",
        "year_num",
    ],
    "dim_location": ["location_key", "state", "city"],
    "dim_manufacturer": ["manufacturer_key", "manufacturer_name"],
    "dim_vehicle": ["vehicle_key", "model_name"],
    "dim_activity": ["activity_key", "activity_type"],
}


def load_required_tables(engine: Engine, schema: str) -> Dict[str, pd.DataFrame]:
    # Load only required scope columns.
    tables: Dict[str, pd.DataFrame] = {}
    for table, cols in REQUIRED_COLUMNS.items():
        quoted_cols = ", ".join(f'"{c}"' for c in cols)
        sql = f'SELECT {quoted_cols} FROM "{schema}"."{table}"'
        frame = pd.read_sql_query(sql, engine)

        # Parse date columns.
        if table in {"fact_ev_activity", "dim_date"}:
            for date_col in ["event_date", "full_date"]:
                if date_col in frame.columns:
                    frame[date_col] = pd.to_datetime(frame[date_col], errors="coerce")

        tables[table] = frame
    return tables


def main() -> None:
    # Load data from Target DB.
    settings = load_settings()
    engine = get_engine()
    tables = load_required_tables(engine, settings.target_schema)

    ensure_reports()
    for table_name, frame in tables.items():
        frame.to_csv(raw_table_path(table_name), index=False)

    print("Stage 01 complete: Data Collection")
    for name, frame in tables.items():
        print(f"  - {name}: {len(frame)} rows")


if __name__ == "__main__":
    main()
