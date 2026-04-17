"""Audit route — returns recent signed receipts."""

from __future__ import annotations

from fastapi import APIRouter, Query

from .state import get_emitter

router = APIRouter()


@router.get("/audit")
def audit(limit: int = Query(50, ge=1, le=500)) -> dict:
    receipts = get_emitter().recent(limit)
    return {"count": len(receipts), "receipts": receipts}
