"""Diagnostics endpoints: diagnoses, predictions, anomalies per asset."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Anomaly, Diagnosis, Prediction
from ..schemas import AnomalyRow, DiagnosisRow, PredictionRow

router = APIRouter(prefix="/api/assets/{asset_id}", tags=["diagnostics"])


def _limit(value: int) -> int:
    return max(1, min(value, 50_000))


@router.get("/diagnoses", response_model=List[DiagnosisRow])
def list_diagnoses(asset_id: str,
                   limit: int = Query(default=1000, ge=1, le=50_000),
                   db: Session = Depends(get_db)):
    return db.scalars(
        select(Diagnosis).where(Diagnosis.asset_id == asset_id)
        .order_by(Diagnosis.ts).limit(_limit(limit))).all()


@router.get("/predictions", response_model=List[PredictionRow])
def list_predictions(asset_id: str,
                     limit: int = Query(default=1000, ge=1, le=50_000),
                     db: Session = Depends(get_db)):
    return db.scalars(
        select(Prediction).where(Prediction.asset_id == asset_id)
        .order_by(Prediction.ts).limit(_limit(limit))).all()


@router.get("/anomalies", response_model=List[AnomalyRow])
def list_anomalies(asset_id: str,
                   limit: int = Query(default=1000, ge=1, le=50_000),
                   db: Session = Depends(get_db)):
    return db.scalars(
        select(Anomaly).where(Anomaly.asset_id == asset_id)
        .order_by(Anomaly.ts).limit(_limit(limit))).all()