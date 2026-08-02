"""
Database engine, session factory, and Base declarative class.

Switch to Postgres by setting DATABASE_URL=postgresql+psycopg://... in .env.
SQLite-specific connect_args are skipped automatically when not on sqlite.
"""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings


def _engine_kwargs() -> dict:
    """SQLite needs check_same_thread=False; Postgres doesn't."""
    if settings.DATABASE_URL.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {}


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
