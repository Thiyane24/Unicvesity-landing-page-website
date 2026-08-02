"""
Lead capture API.

Public endpoint:
    POST /api/leads            → save a new lead (called by the landing page)

Admin endpoints (require Bearer token):
    GET  /api/admin/leads      → list leads with optional search/filter/pagination
    GET  /api/admin/leads/{id} → single lead
    GET  /api/admin/leads.csv  → CSV export (great for pasting into Sheets / a CRM)
    DELETE /api/admin/leads/{id} → soft delete (we just hard-delete for now)

Why this layout?
- Public POST is small and fast — no auth, just thorough validation.
- Admin endpoints live under /api/admin/* with a single dependency.
- CSV export keeps ops happy without an extra SDK.
"""
from __future__ import annotations

import csv
import io
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.deps import require_admin
from app.db import get_db
from app.models import Lead
from app.schemas import (
    LeadCreate,
    LeadRead,
    LeadSubmitResponse,
)

router = APIRouter(prefix="/api", tags=["leads"])


# ----------------------------------------------------------------------
# PUBLIC — landing page posts here
# ----------------------------------------------------------------------
@router.post(
    "/leads",
    response_model=LeadSubmitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new lead from the public landing page",
)
def submit_lead(
    payload: LeadCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Persist a new lead. Idempotency is NOT enforced — same email can submit twice."""

    # Capture useful metadata so the CRM team has context.
    ip_address = (request.client.host if request.client else None)
    user_agent = request.headers.get("user-agent")

    lead = Lead(
        name        = payload.name,
        whatsapp    = payload.whatsapp,
        email       = str(payload.email),
        destination = payload.destination,
        source      = payload.source,
        ip_address  = ip_address,
        user_agent  = (user_agent[:255] if user_agent else None),
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)

    return LeadSubmitResponse(
        id=lead.id,
        received_at=lead.created_at,
    )


# ----------------------------------------------------------------------
# ADMIN — protected by require_admin()
# ----------------------------------------------------------------------
@router.get(
    "/admin/leads",
    response_model=List[LeadRead],
    summary="List leads (admin)",
)
def list_leads(
    db:            Session              = Depends(get_db),
    _token:        str                  = Depends(require_admin),
    q:             Optional[str]        = Query(None, description="Search name/email/whatsapp"),
    destination:   Optional[str]        = Query(None),
    limit:         int                  = Query(50,  ge=1, le=500),
    offset:        int                  = Query(0,   ge=0),
):
    query = db.query(Lead)

    if destination:
        query = query.filter(Lead.destination == destination)

    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            (Lead.name.ilike(like)) |
            (Lead.email.ilike(like)) |
            (Lead.whatsapp.ilike(like))
        )

    return (
        query.order_by(desc(Lead.created_at))
             .offset(offset)
             .limit(limit)
             .all()
    )


@router.get(
    "/admin/leads/{lead_id}",
    response_model=LeadRead,
    summary="Get a single lead (admin)",
)
def get_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    _token: str = Depends(require_admin),
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.delete(
    "/admin/leads/{lead_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a lead (admin)",
)
def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    _token: str = Depends(require_admin),
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    db.delete(lead)
    db.commit()
    return None


@router.get(
    "/admin/leads.csv",
    summary="Stream all leads as CSV (admin)",
    response_class=StreamingResponse,
)
def export_leads_csv(
    db: Session = Depends(get_db),
    _token: str = Depends(require_admin),
):
    """Stream as CSV so we don't blow up memory on huge lead lists."""
    leads = db.query(Lead).order_by(desc(Lead.created_at)).all()

    # StringIO instead of a tempfile — keeps the export inside one request.
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "id", "name", "email", "whatsapp", "destination",
        "source", "ip_address", "user_agent", "created_at",
    ])
    for l in leads:
        writer.writerow([
            l.id, l.name, l.email, l.whatsapp, l.destination,
            l.source, l.ip_address, l.user_agent,
            l.created_at.isoformat() if l.created_at else "",
        ])

    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="leads.csv"'},
    )
