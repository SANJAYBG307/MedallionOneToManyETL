from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from _common import load_environment

ORDER = [
    "01_data_collection.py",
    "02_data_profiling.py",
    "03_data_quality.py",
    "04_data_cleaning.py",
    "05_data_transformation.py",
    "06_data_preparation.py",
    "07_eda.py",
    "08_data_analysis.py",
    "09_data_visualization.py",
]


def main() -> None:
    # Load env first so all child scripts get Target DB creds.
    load_environment()

    # Run all stages in order.
    for script_name in ORDER:
        script_path = SCRIPTS_DIR / script_name
        print(f"\nRunning {script_name} ...")
        result = subprocess.run([sys.executable, str(script_path)], check=False)
        if result.returncode != 0:
            raise SystemExit(f"Stopped at {script_name} (exit code {result.returncode})")

    print("\nAll stages completed.")


if __name__ == "__main__":
    main()
