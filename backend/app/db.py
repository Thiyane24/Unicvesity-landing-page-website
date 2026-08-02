"""
Database engine, session factory, and Base declarative class.

Switch to Postgres by setting DATABASE_URL=postgresql+psycopg://... in .env.
SQLite-specific connect_args are skipped automatically when not on sqlite.

Production Postgres tips:
- For Supabase's pooler (port 6543) the URL MUST include ?sslmode=require.
- connect_timeout prevents a worker from hanging forever if the DB is unreachable.
- pool_pre_ping transparently recycles dead connections (Supavisor occasionally drops them).
"""
from __future__ import annotations

import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

logger = logging.getLogger("unicvesity.db")


def _engine_kwargs() -> dict:
    """Engine kwargs differ between SQLite and Postgres."""
    if settings.DATABASE_URL.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    # Postgres — fail fast on unreachable DB rather than hanging the worker.
    return {
        "connect_args": {"connect_timeout": 10},
        "pool_size": 5,
        "max_overflow": 5,
        "pool_recycle": 280,   # recycle before Supavisor's typical 5-min idle drop
    }


# Mask password in any startup log lines
_safe_url = settings.DATABASE_URL
if "@" in _safe_url:
    _safe_url = _safe_url.split("@", 1)[0].rsplit(":", 1)[0] + "@***"
logger.info("DB engine target: %s", _safe_url)

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    **_engine_kwargs(),
)

# Autocommit=False, autoflush=False — standard pattern, lets FastAPI deps
# control transaction boundaries for predictable tests and error handling.
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# Single shared base for all ORM models
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that yields a database session and closes it after the request.

    Usage in a route:
        @router.get(...)
        def list_leads(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
