"""
Application configuration loaded from environment variables / .env.

Kept deliberately tiny — no secrets manager, no cloud coupling.
Swap to pydantic-settings' SettingsConfigDict if you outgrow this.
"""
from __future__ import annotations

import os
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized settings for the FastAPI app."""

    # Pydantic-settings reads from .env if present
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---- Database ----
    # Default to a local SQLite file so the app boots with zero config.
    # Production: DATABASE_URL=postgresql+psycopg://user:pass@host/dbname
    DATABASE_URL: str = "sqlite:///./leads.db"

    # ---- CORS ----
    # Comma-separated list, parsed into a list[str] below.
    ALLOWED_ORIGINS: str = (
        "http://localhost:5500,"
        "http://127.0.0.1:5500,"
        "http://localhost:8000,"
        "http://127.0.0.1:8000"
    )

    # ---- Admin auth ----
    ADMIN_TOKEN: str = "change-me-to-a-long-random-string"

    # ---- Helpers ----
    def origins_list(self) -> List[str]:
        """Return ALLOWED_ORIGINS as a real list[str] for FastAPI."""
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


# Singleton — import this everywhere: `from app.config import settings`
settings = Settings()
