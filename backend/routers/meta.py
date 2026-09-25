"""Meta endpoints: health check and experiment catalogue."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import app_version
from ..models import Experiment
from ..schemas import ExperimentRow, HealthResponse

router = APIRouter(tags=["meta"])


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)):
    db_ok = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:  # pragma: no cover - database unreachable
        db_ok = "error"
    return HealthResponse(status="ok", db=db_ok, version=app_version())


@router.get("/api/experiments", response_model=List[ExperimentRow])
def list_experiments(db: Session = Depends(get_db)):
    return db.scalars(select(Experiment).order_by(Experiment.created_at)).all()