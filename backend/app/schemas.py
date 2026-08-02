"""
Pydantic request/response schemas.

These are the "DTO" layer — what the API accepts and what it returns.
Keep them separate from ORM models so DB schema can evolve without
breaking the public API contract.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ---------------------------------------------------------------------
# Allowed destinations — must match the <select> in index.html exactly,
# otherwise the API rejects the submission with a 422.
# ---------------------------------------------------------------------
ALLOWED_DESTINATIONS = {
    "UK", "USA", "Australia", "Canada", "Europe", "Other",
    # Frontend dropdown <option value="MY"> maps Malaysia onto the FULL NAME
    # so it survives unchanged from other destinations in the DB.
    "MY",
}


class LeadBase(BaseModel):
    """Fields shared by input and output models."""

    name:        str = Field(..., min_length=2, max_length=120)
    whatsapp:    str = Field(..., min_length=7,  max_length=40)
    email:       EmailStr
    destination: str = Field(...)

    @field_validator("destination")
    @classmethod
    def _dest_allowed(cls, v: str) -> str:
        if v not in ALLOWED_DESTINATIONS:
            raise ValueError(
                f"destination must be one of {sorted(ALLOWED_DESTINATIONS)}"
            )
        return v

    @field_validator("name")
    @classmethod
    def _name_strip(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("name too short")
        return v


class LeadCreate(LeadBase):
    """Payload posted by the public landing page."""

    source: Optional[str] = Field(default=None, max_length=80)
    lang:   Optional[str] = Field(default=None, max_length=8)


class LeadRead(LeadBase):
    """Returned by GET /api/admin/leads."""

    model_config = ConfigDict(from_attributes=True)

    id:         int
    source:     Optional[str] = None
    lang:       Optional[str] = None
    created_at: datetime
    updated_at: datetime


class LeadSubmitResponse(BaseModel):
    """Lightweight ack sent back to the public form on success."""

    ok:         bool = True
    id:         int
    message:    str = "We've received your details. Check your WhatsApp!"
    received_at: datetime


class HealthResponse(BaseModel):
    ok: bool = True
    service: str = "unicvesity-leads"
    db: str = "connected"
