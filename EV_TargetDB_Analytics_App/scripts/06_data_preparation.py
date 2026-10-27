from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import ensure_reports, model_path, prepared_path


def prepare_for_analysis(model: pd.DataFrame) -> pd.DataFrame:
    # Prepare final dataset for analysis.
    prepared = model.copy()

    if "full_date" in prepared.columns:
        prepared["full_date"] = pd.to_datetime(prepared["full_date"], errors="coerce")
    if "event_date" in prepared.columns:
        prepared["event_date"] = pd.to_datetime(prepared["event_date"], errors="coerce")

    for col in ["state", "city", "manufacturer_name", "model_name", "activity_type"]:
        if col in prepared.columns:
            prepared[col] = prepared[col].fillna("Unknown")

    for col in ["revenue_amount", "final_price"]:
        if col in prepared.columns:
            prepared[col] = pd.to_numeric(prepared[col], errors="coerce").fillna(0)

    return prepared


def main() -> None:
    # Prepare final analysis dataset.
    model = pd.read_csv(model_path())
    prepared = prepare_for_analysis(model)

    ensure_reports()
    prepared.to_csv(prepared_path(), index=False)

    print("Stage 06 complete: Data Preparation")
    print(f"  - Prepared rows: {len(prepared)}")


if __name__ == "__main__":
    main()
