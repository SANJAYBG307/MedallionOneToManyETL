from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import CSV_DIR, ensure_reports, prepared_path


def run_eda(prepared: pd.DataFrame) -> dict[str, pd.DataFrame]:
    # Create beginner-friendly EDA outputs.
    out: dict[str, pd.DataFrame] = {}

    numeric_cols = [c for c in ["revenue_amount", "final_price"] if c in prepared.columns]
    if numeric_cols:
        out["numeric_summary"] = prepared[numeric_cols].describe().transpose().reset_index(names="column")
    else:
        out["numeric_summary"] = pd.DataFrame(
            columns=["column", "count", "mean", "std", "min", "25%", "50%", "75%", "max"]
        )

    if "activity_type" in prepared.columns:
        out["activity_mix"] = (
            prepared.groupby("activity_type", dropna=False)["transaction_id"]
            .nunique()
            .reset_index(name="distinct_transactions")
            .sort_values("distinct_transactions", ascending=False)
        )
    else:
        out["activity_mix"] = pd.DataFrame(columns=["activity_type", "distinct_transactions"])

    if "state" in prepared.columns:
        out["top_states"] = (
            prepared.groupby("state", dropna=False)["transaction_id"]
            .nunique()
            .reset_index(name="distinct_transactions")
            .sort_values("distinct_transactions", ascending=False)
            .head(10)
        )
    else:
        out["top_states"] = pd.DataFrame(columns=["state", "distinct_transactions"])

    return out


def main() -> None:
    # Create simple EDA outputs.
    prepared = pd.read_csv(prepared_path())
    eda_outputs = run_eda(prepared)

    ensure_reports()
    for name, frame in eda_outputs.items():
        frame.to_csv(CSV_DIR / f"07_eda_{name}.csv", index=False)

    print("Stage 07 complete: EDA")
    print("  - reports/csv/07_eda_*.csv")


if __name__ == "__main__":
    main()
