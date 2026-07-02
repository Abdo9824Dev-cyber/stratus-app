"""
Database layer.

The connection is built ENTIRELY from environment variables. This is the key
design decision for this project: running locally vs. running on Google Cloud
later requires changing ONLY these env vars, never this code.

Local (docker-compose):   DB_HOST=db        DB_PASSWORD=localpass
Cloud (next phase):        DB_HOST=<Cloud SQL private IP>
                           DB_PASSWORD=<injected from Secret Manager>
"""
import os
import time

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

# --- Read connection details from the environment (with local-friendly defaults) ---
DB_USER = os.getenv("DB_USER", "store")
DB_PASSWORD = os.getenv("DB_PASSWORD", "localpass")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "store")

# A full URL can override the individual parts (handy in some cloud setups).
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def wait_for_db(retries: int = 10, delay: float = 2.0) -> None:
    """Wait for the database to accept connections (useful on first compose-up)."""
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except Exception as exc:  # noqa: BLE001 - we want to retry on any connection error
            last_error = exc
            print(f"[db] not ready (attempt {attempt}/{retries}): {exc}")
            time.sleep(delay)
    raise RuntimeError(f"Database never became available: {last_error}")


def db_is_healthy() -> bool:
    """Lightweight check used by the /healthz endpoint."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001
        return False
