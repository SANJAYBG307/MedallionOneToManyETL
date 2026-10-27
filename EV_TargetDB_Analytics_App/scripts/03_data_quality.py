from __future__ import annotations

from pathlib import Path
import sys
from typing import Dict

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import load_settings
from scripts._common import TABLE_NAMES, CSV_DIR, ensure_reports, raw_table_path


def _check_orphans(fact: pd.DataFrame, dim: pd.DataFrame, fact_key: str, dim_key: str) -> int:
    # Count fact keys not present in dimension.
    valid = set(dim[dim_key].dropna().tolist())
    return int((~fact[fact_key].isin(valid)).sum())


def run_quality_checks(
    tables: Dict[str, pd.DataFrame], expected_activities: tuple[str, ...]
) -> pd.DataFrame:
    fact = tables["fact_ev_activity"]
    dim_activity = tables["dim_activity"]

    checks: list[dict[str, object]] = []

    null_txn = int(fact["transaction_id"].isna().sum())
    checks.append(
        {
            "check_name": "transaction_id_non_null",
            "passed": null_txn == 0,
            "failed_count": null_txn,
            "details": "transaction_id must be non-null",
        }
    )

    invalid_revenue = int((pd.to_numeric(fact["revenue_amount"], errors="coerce") < 0).sum())
    checks.append(
        {
            "check_name": "revenue_non_negative",
            "passed": invalid_revenue == 0,
            "failed_count": invalid_revenue,
            "details": "revenue_amount must be >= 0",
        }
    )

    bool_ok = fact["warranty_claim_flag"].dropna().isin([True, False]).all()
    checks.append(
        {
            "check_name": "warranty_flag_boolean",
            "passed": bool(bool_ok),
            "failed_count": 0 if bool_ok else int(fact["warranty_claim_flag"].notna().sum()),
            "details": "warranty_claim_flag should be boolean when present",
        }
    )

    fk_map = [
        ("date_key", "dim_date", "date_key"),
        ("location_key", "dim_location", "location_key"),
        ("manufacturer_key", "dim_manufacturer", "manufacturer_key"),
        ("vehicle_key", "dim_vehicle", "vehicle_key"),
        ("activity_key", "dim_activity", "activity_key"),
    ]

    for fk_col, dim_name, dim_key in fk_map:
        orphans = _check_orphans(fact, tables[dim_name], fk_col, dim_key)
        checks.append(
            {
                "check_name": f"fk_integrity_{fk_col}",
                "passed": orphans == 0,
                "failed_count": orphans,
                "details": f"{fk_col} values must map to {dim_name}.{dim_key}",
            }
        )

    actual_activities = set(dim_activity["activity_type"].dropna().astype(str).str.strip())
    expected_set = set(expected_activities)
    missing = sorted(expected_set - actual_activities)
    extra = sorted(actual_activities - expected_set)
    passed = not missing and not extra

    checks.append(
        {
            "check_name": "activity_label_conformance",
            "passed": passed,
            "failed_count": len(missing) + len(extra),
            "details": f"missing={missing}; extra={extra}",
        }
    )

    return pd.DataFrame(checks)


def main() -> None:
    # Check data quality rules.
    settings = load_settings()
    tables: Dict[str, pd.DataFrame] = {}
    for table_name in TABLE_NAMES:
        tables[table_name] = pd.read_csv(raw_table_path(table_name))

    dq = run_quality_checks(tables, settings.expected_activities)

    ensure_reports()
    dq.to_csv(CSV_DIR / "03_dq_summary.csv", index=False)

    print("Stage 03 complete: Data Quality")
    print("  - reports/csv/03_dq_summary.csv")


if __name__ == "__main__":
    main()
