"""
SQLAlchemy ORM models.

Right now there's just one: `Lead`. If you need Users, Universities,
or Notes later, add them here as classes inheriting Base.
"""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, DateTime, Index, Integer, String, Text

from app.db import Base


class Lead(Base):
    """A single submission from the landing-page lead form."""

    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)

    # Form fields
    name = Column(String(120), nullable=False, index=True)
    whatsapp = Column(String(40), nullable=False, index=True)
    email = Column(String(254), nullable=False, index=True)  # RFC 5321 max length
    destination = Column(String(40), nullable=False, index=True)

    # Where the lead came from (UTM, referrer, etc.)
    source = Column(String(80), nullable=True, index=True)
    user_agent = Column(String(255), nullable=True)
    ip_address = Column(String(64), nullable=True)
    notes = Column(Text, nullable=True)

    # Lifecycle
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Compound index for common admin queries ("last 50 leads in UK")
    __table_args__ = (
        Index("ix_leads_destination_created", "destination", "created_at"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Lead id={self.id} name={self.name!r} email={self.email!r}>"
