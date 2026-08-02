# =====================================================================
# Unicvesity Worldwide — Lead API image
# =====================================================================
# Multi-stage build:
#   1) "builder" installs deps into a venv
#   2) "runtime" copies that venv into a slim image + runs gunicorn
#
# Benefits:
#   - Smaller final image (no compilers, no pip cache)
#   - Reproducible installs from requirements.txt
#   - Runs as a non-root user (security baseline)
# =====================================================================

# ---------- Stage 1: builder ----------
FROM python:3.12-slim AS builder

# Telemetry off keeps our build logs clean.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install build deps first; pinned versions in requirements.txt keep this
# deterministic.  We install into a venv so we can copy it wholesale later.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt


# ---------- Stage 2: runtime ----------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    WORKERS=2

# Install only what we need at runtime: curl for healthchecks, tini for
# clean SIGTERM propagation (FastAPI + Postgres must shut down gracefully).
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl tini \
 && rm -rf /var/lib/apt/lists/*

# Non-root user — defense in depth.
RUN groupadd --system app && useradd --system --gid app --home /app app
WORKDIR /app

# Copy the prepared virtual environment from the builder.
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy the application source.
COPY --chown=app:app app ./app

# Persistent SQLite dir (mounted as a volume in compose).
RUN mkdir -p /app/data && chown -R app:app /app/data
ENV DATABASE_URL="sqlite:////app/data/leads.db"

USER app

EXPOSE 8000

# Container-level healthcheck — hits /api/health which also pings the DB.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -fsS http://127.0.0.1:${PORT}/api/health || exit 1

# tini reaps zombies and forwards signals; gunicorn (uvicorn worker) runs the API.
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["sh", "-c", "gunicorn -k uvicorn.workers.UvicornWorker -w ${WORKERS} -b 0.0.0.0:${PORT} app.main:app --access-logfile - --error-logfile -"]
