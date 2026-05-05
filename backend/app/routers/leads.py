"""Leads router — WhatsApp lead capture endpoint."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Lead
from app.schemas import LeadRequest

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/leads", tags=["leads"])
async def create_lead(
    request: LeadRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Capture a WhatsApp lead and persist it to the database.

    Args:
        request: Lead data from the frontend capture form.
        db: Database session (injected).

    Returns:
        Dict with status and the new lead ID.
    """
    lead = Lead(
        session_id=request.session_id,
        name=request.name,
        whatsapp=request.whatsapp,
        current_car=request.current_car,
        budget_clp=request.budget_clp,
        city=request.city,
        buy_timeframe=request.buy_timeframe,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    logger.info("Saved lead id=%d session=%s", lead.id, request.session_id)
    return {"status": "ok", "lead_id": lead.id}
