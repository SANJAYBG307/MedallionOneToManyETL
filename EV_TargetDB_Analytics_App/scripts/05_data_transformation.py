from __future__ import annotations

from pathlib import Path
import sys
from typing import Dict

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import TABLE_NAMES, ensure_reports, clean_table_path, model_path


def build_canonical_model(tables: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    # Build one joined model from fact and dimensions.
    fact = tables["fact_ev_activity"].copy()

    date_dim = tables["dim_date"][[
        "date_key",
        "full_date",
        "month_num",
        "month_name",
        "quarter_num",
        "year_num",
    ]].copy()
    location_dim = tables["dim_location"][["location_key", "state", "city"]].copy()
    manu_dim = tables["dim_manufacturer"][["manufacturer_key", "manufacturer_name"]].copy()
    vehicle_dim = tables["dim_vehicle"][["vehicle_key", "model_name"]].copy()
    activity_dim = tables["dim_activity"][["activity_key", "activity_type"]].copy()

    model = fact.merge(date_dim, on="date_key", how="left")
    model = model.merge(location_dim, on="location_key", how="left")
    model = model.merge(manu_dim, on="manufacturer_key", how="left")
    model = model.merge(vehicle_dim, on="vehicle_key", how="left")
    model = model.merge(activity_dim, on="activity_key", how="left")

    return model


def main() -> None:
    # Join fact and dimensions.
    cleaned: Dict[str, pd.DataFrame] = {}
    for table_name in TABLE_NAMES:
        cleaned[table_name] = pd.read_csv(clean_table_path(table_name))

    model = build_canonical_model(cleaned)

    ensure_reports()
    model.to_csv(model_path(), index=False)

    print("Stage 05 complete: Data Transformation")
    print(f"  - Model rows: {len(model)}")


if __name__ == "__main__":
    main()
