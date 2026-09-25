"""Maintenance endpoints: plans and per-asset events."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import MaintenanceEvent, MaintenancePlan
from ..schemas import MaintenanceEventRow, MaintenancePlanRow

router = APIRouter(prefix="/api", tags=["maintenance"])


@router.get("/maintenance/plans", response_model=List[MaintenancePlanRow])
def list_plans(latest: bool = Query(default=False),
               db: Session = Depends(get_db)):
    stmt = select(MaintenancePlan).order_by(MaintenancePlan.generated_at.desc())
    if latest:
        stmt = stmt.limit(1)
    return db.scalars(stmt).all()


@router.get("/maintenance/events", response_model=List[MaintenanceEventRow])
def list_events(db: Session = Depends(get_db)):
    return db.scalars(
        select(MaintenanceEvent).order_by(MaintenanceEvent.scheduled_at)).all()


@router.get("/assets/{asset_id}/maintenance-events",
            response_model=List[MaintenanceEventRow])
def list_asset_events(asset_id: str, db: Session = Depends(get_db)):
    return db.scalars(
        select(MaintenanceEvent).where(MaintenanceEvent.asset_id == asset_id)
        .order_by(MaintenanceEvent.scheduled_at)).all()