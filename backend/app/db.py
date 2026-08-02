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
from urllib.parse import urlsplit, urlunsplit, quote

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

logger = logging.getLogger("unicvesity.db")


def _normalize_url(url: str) -> str:
    """
    Make a DATABASE_URL robust against common deployment pitfalls:

    1. Force the psycopg v3 driver.  SQLAlchemy 2.x falls back to psycopg2 when
       no driver is in the URL and psycopg2 isn't installed, which crashes
       the worker with `ModuleNotFoundError: No module named 'psycopg2'`.
    2. URL-encode the password (so '!', '@', '#', etc. don't break parsers).
    3. Preserve any existing query string (sslmode, etc.).
    """
    parts = urlsplit(url)
    scheme = parts.scheme
    if scheme == "postgresql":
        scheme = "postgresql+psycopg"
    elif scheme == "postgres":
        scheme = "postgresql+psycopg"

    # Encode password (parts[1]) but leave user as-is.
    if "@" in parts.netloc:
        userinfo, hostinfo = parts.netloc.rsplit("@", 1)
        if ":" in userinfo:
            user, _, password = userinfo.partition(":")
            password = quote(password, safe="")
            netloc = f"{user}:{password}@{hostinfo}"
        else:
            netloc = parts.netloc
    else:
        netloc = parts.netloc

    return urlunsplit((scheme, netloc, parts.path, parts.query, parts.fragment))


DATABASE_URL = _normalize_url(settings.DATABASE_URL)


def _engine_kwargs() -> dict:
    """Engine kwargs differ between SQLite and Postgres."""
    if DATABASE_URL.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    # Postgres — fail fast on unreachable DB rather than hanging the worker.
    return {
        "connect_args": {"connect_timeout": 10},
        "pool_size": 5,
        "max_overflow": 5,
        "pool_recycle": 280,   # recycle before Supavisor's typical 5-min idle drop
    }


# Mask password in any startup log lines
_safe_url = DATABASE_URL
if "@" in _safe_url:
    _safe_url = _safe_url.split("@", 1)[0].rsplit(":", 1)[0] + "@***"
logger.info("DB engine target: %s", _safe_url)

engine = create_engine(
    DATABASE_URL,
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
