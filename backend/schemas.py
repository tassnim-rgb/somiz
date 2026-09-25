"""Pydantic schemas: request validation + response serialisation.

All response schemas read from ORM objects (``from_attributes``). The
POST payloads validate input (the Phase 7 "validation" gate): an invalid
body is rejected with 422 before touching the database.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- assets ----------------------------------------------------------
class AssetSummary(ORMModel):
    id: int
    asset_id: str
    asset_type: str
    name: str


class AssetDetail(ORMModel):
    id: int
    asset_id: str
    asset_type: str
    name: str
    description: Optional[str] = None
    params_json: Dict[str, Any] = Field(default_factory=dict)
    criticality_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class AssetCreate(BaseModel):
    asset_id: str = Field(min_length=1, max_length=32, pattern=r"^[A-Za-z0-9_-]+$")
    asset_type: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=128)
    description: Optional[str] = None
    params_json: Dict[str, Any] = Field(default_factory=dict)
    criticality_json: Dict[str, Any] = Field(default_factory=dict)


# --- measurements / sensors -------------------------------------------
class SensorInfo(ORMModel):
    tag: str
    name: str
    unit: Optional[str] = None
    kind: str


class SensorRow(SensorInfo):
    id: int


class MeasurementRow(BaseModel):
    ts: float
    tag: str
    value: Optional[float] = None
    quality_flag: str


class MeasurementsResponse(BaseModel):
    asset_id: str
    total: int
    rows: List[MeasurementRow]


# --- diagnostics ------------------------------------------------------
class DiagnosisRow(ORMModel):
    id: int
    ts: float
    fault_type: str
    probability: Optional[float] = None
    severity_estimate: Optional[float] = None
    affected_signals_json: Dict[str, Any] = Field(default_factory=dict)
    method: str
    model_version: str


class PredictionRow(ORMModel):
    id: int
    ts: float
    health_index: Optional[float] = None
    rul_estimate: Optional[float] = None
    rul_lower: Optional[float] = None
    rul_upper: Optional[float] = None
    confidence: Optional[float] = None
    model_version: str


class AnomalyRow(ORMModel):
    id: int
    ts: float
    score: Optional[float] = None
    threshold: Optional[float] = None
    is_detected: bool
    true_onset_ts: Optional[float] = None
    detection_delay: Optional[float] = None
    false_alarm_flag: bool


# --- maintenance ------------------------------------------------------
class MaintenanceEventRow(ORMModel):
    id: int
    asset_id: str
    scheduled_at: Optional[datetime] = None
    performed_at: Optional[datetime] = None
    action_type: str
    cost: Optional[float] = None
    duration_h: Optional[float] = None
    outcome: Optional[str] = None


class MaintenancePlanRow(ORMModel):
    id: int
    generated_at: datetime
    horizon_days: int
    objective_value: Optional[float] = None
    solver: str
    plan_json: Dict[str, Any] = Field(default_factory=dict)
    constraints_json: Dict[str, Any] = Field(default_factory=dict)


class ExperimentRow(ORMModel):
    id: int
    name: str
    config_json: Dict[str, Any] = Field(default_factory=dict)
    metrics_json: Dict[str, Any] = Field(default_factory=dict)
    artifacts_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


# --- health -----------------------------------------------------------
class HealthResponse(BaseModel):
    status: str
    db: str
    version: str