"""
FastAPI entrypoint.

Run (dev):
    cd backend
    uvicorn app.main:app --reload --port 8000

The app:
- Creates tables on startup (no separate migration step needed for SQLite).
- Configures CORS so the static HTML landing page can call /api/leads.
- Routes requests to /api/* (defined in app/routes/*).
"""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.db import Base, engine
from app.routes.leads import router as leads_router
from app.schemas import HealthResponse

logger = logging.getLogger("unicvesity")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s :: %(message)s")


# ---------------------------------------------------------------------
# App
# ---------------------------------------------------------------------
app = FastAPI(
    title="Unicvesity Worldwide — Lead Capture API",
    description=(
        "Public POST /api/leads saves new landing-page leads to a SQL database. "
        "Admin routes under /api/admin/* require a Bearer token."
    ),
    version="1.0.0",
)


# ---------------------------------------------------------------------
# CORS — so the static HTML page can POST without browser blocking
# ---------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------
@app.on_event("startup")
def _startup() -> None:
    """Create tables on first run. Safe to call repeatedly."""
    # Importing models here ensures they're registered with Base.metadata
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # Quick DB ping so any DB-down issues fail loudly at boot instead of on first request
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection OK")
    except Exception as exc:  # pragma: no cover
        logger.error("❌ Database connection FAILED: %s", exc)
        # Do NOT re-raise: keep the worker alive so /api/health can return a
        # useful 503 instead of crashing the gunicorn boot loop.


# ---------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------
app.include_router(leads_router)


# ---------------------------------------------------------------------
# Health endpoint — for uptime checkers / load balancers
# ---------------------------------------------------------------------
@app.get("/api/health", response_model=HealthResponse, tags=["ops"])
def health():
    db_state = "connected"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        db_state = "down"
    return HealthResponse(db=db_state)


@app.get("/", tags=["ops"])
def root():
    return {"service": "unicvesity-leads", "docs": "/docs"}
