from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
import os


@dataclass(frozen=True)
class Settings:
    target_schema: str
    expected_activities: tuple[str, ...]


def load_settings() -> Settings:
    # Load .env from current project and parent workspace if present.
    here = Path(__file__).resolve().parents[1]
    parent = here.parent
    load_dotenv(here / ".env", override=False)
    load_dotenv(parent / ".env", override=False)

    return Settings(
        target_schema=os.getenv("TARGET_SCHEMA", "public"),
        expected_activities=("Charging", "Production", "Sale", "Service"),
    )
