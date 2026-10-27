from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
MAIN_ROOT = ROOT.parent
REPORTS_DIR = ROOT / "reports"
CSV_DIR = REPORTS_DIR / "csv"
FIGURES_DIR = REPORTS_DIR / "figures"

TABLE_NAMES = (
    "fact_ev_activity",
    "dim_date",
    "dim_location",
    "dim_manufacturer",
    "dim_vehicle",
    "dim_activity",
)


def load_environment() -> None:
    """Load .env from analytics app and main project.

    Main project values are loaded last so Target DB creds come from main .env.
    """
    load_dotenv(ROOT / ".env", override=False)
    load_dotenv(MAIN_ROOT / ".env", override=True)

    # Keep working directory stable for relative paths.
    os.chdir(MAIN_ROOT)


def ensure_reports() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def raw_table_path(table_name: str) -> Path:
    return CSV_DIR / f"01_{table_name}.csv"


def clean_table_path(table_name: str) -> Path:
    return CSV_DIR / f"04_{table_name}_clean.csv"


def model_path() -> Path:
    return CSV_DIR / "05_model.csv"


def prepared_path() -> Path:
    return CSV_DIR / "06_prepared.csv"


def bq_path(bq_name: str) -> Path:
    return CSV_DIR / f"08_{bq_name}.csv"
