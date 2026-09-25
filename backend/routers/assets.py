"""Asset catalogue endpoints: list, detail, sensors, measurements."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Asset, Measurement, Sensor
from ..schemas import (
    AssetCreate,
    AssetDetail,
    AssetSummary,
    MeasurementRow,
    MeasurementsResponse,
    SensorInfo,
)

router = APIRouter(prefix="/api/assets", tags=["assets"])


def _get_asset(db: Session, asset_id: str) -> Asset:
    asset = db.scalar(select(Asset).where(Asset.asset_id == asset_id))
    if asset is None:
        raise HTTPException(status_code=404, detail=f"asset {asset_id!r} not found")
    return asset


@router.get("", response_model=List[AssetSummary])
def list_assets(db: Session = Depends(get_db)):
    return db.scalars(select(Asset).order_by(Asset.asset_id)).all()


@router.post("", response_model=AssetDetail, status_code=201)
def create_asset(payload: AssetCreate, db: Session = Depends(get_db)):
    existing = db.scalar(select(Asset).where(Asset.asset_id == payload.asset_id))
    if existing is not None:
        raise HTTPException(status_code=409,
                            detail=f"asset {payload.asset_id!r} already exists")
    asset = Asset(**payload.model_dump())
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@router.get("/{asset_id}", response_model=AssetDetail)
def get_asset(asset_id: str, db: Session = Depends(get_db)):
    return _get_asset(db, asset_id)


@router.get("/{asset_id}/sensors", response_model=List[SensorInfo])
def get_asset_sensors(asset_id: str, db: Session = Depends(get_db)):
    _get_asset(db, asset_id)
    return db.scalars(select(Sensor).where(Sensor.asset_id == asset_id)
                      .order_by(Sensor.tag)).all()


@router.get("/{asset_id}/measurements", response_model=MeasurementsResponse)
def get_asset_measurements(
    asset_id: str,
    tag: Optional[str] = Query(default=None),
    limit: int = Query(default=1000, ge=1, le=100_000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    _get_asset(db, asset_id)
    stmt = (select(Measurement, Sensor.tag)
            .join(Sensor, Measurement.sensor_id == Sensor.id)
            .where(Measurement.asset_id == asset_id))
    if tag is not None:
        stmt = stmt.where(Sensor.tag == tag)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.execute(stmt.order_by(Measurement.ts).offset(offset).limit(limit)).all()
    return MeasurementsResponse(
        asset_id=asset_id,
        total=int(total or 0),
        rows=[
            MeasurementRow(ts=m.ts, tag=t, value=m.value,
                           quality_flag=m.quality_flag)
            for m, t in rows
        ],
    )