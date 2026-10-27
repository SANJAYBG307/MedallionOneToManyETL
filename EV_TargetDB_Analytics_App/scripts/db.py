from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def _dsn_from_env() -> str:
    dsn = os.getenv("NEON_DSN", "").strip()
    if dsn:
        if dsn.startswith("postgresql://"):
            return dsn.replace("postgresql://", "postgresql+psycopg2://", 1)
        return dsn

    host = os.getenv("NEON_HOST", "").strip()
    port = os.getenv("NEON_PORT", "5432").strip()
    db = os.getenv("NEON_DB", "").strip()
    user = os.getenv("NEON_USER", "").strip()
    pwd = os.getenv("NEON_PASSWORD", "").strip()

    if not all([host, db, user, pwd]):
        raise ValueError("Missing Target DB connection values. Set NEON_DSN or explicit NEON_* vars.")

    return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}"


def get_engine() -> Engine:
    dsn = _dsn_from_env()
    return create_engine(dsn, pool_pre_ping=True)
