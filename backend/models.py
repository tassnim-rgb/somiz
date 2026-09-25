"""ORM models: the SOMIZ SQLite schema (SQLAlchemy 2.x typed style).

Mirrors the 10-table schema proposed in PROJECT_AUDIT.md section 11.5
(assets, sensors, measurements, faults, anomalies, diagnoses,
predictions, maintenance_events, maintenance_plans, experiments).
PostgreSQL-ready: nothing here is SQLite-specific.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    asset_type: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[Optional[str]] = mapped_column(Text, default=None)
    params_json: Mapped[dict] = mapped_column(JSON, default=dict)
    criticality_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    retired_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)


class Sensor(Base):
    __tablename__ = "sensors"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.asset_id"), index=True)
    tag: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(128))
    unit: Mapped[Optional[str]] = mapped_column(String(16), default=None)
    kind: Mapped[str] = mapped_column(String(32))          # vibration / thermal / hydraulic / electrical
    meta_json: Mapped[dict] = mapped_column(JSON, default=dict)


class Measurement(Base):
    __tablename__ = "measurements"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.asset_id"), index=True)
    sensor_id: Mapped[int] = mapped_column(ForeignKey("sensors.id"))
    ts: Mapped[float] = mapped_column(Float, index=True)   # seconds since run start
    value: Mapped[Optional[float]] = mapped_column(Float, default=None)
    quality_flag: Mapped[str] = mapped_column(String(16), default="OK")


class Fault(Base):
    __tablename__ = "faults"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.asset_id"), index=True)
    fault_type: Mapped[str] = mapped_column(String(32))
    onset_ts: Mapped[Optional[float]] = mapped_column(Float, default=None)
    severity: Mapped[float] = mapped_column(Float, default=0.0)
    progression_params: Mapped[dict] = mapped_column(JSON, default=dict)
    ground_truth_state: Mapped[str] = mapped_column(String(32), default="simulated")
    notes: Mapped[Optional[str]] = mapped_column(Text, default=None)


class Anomaly(Base):
    __tablename__ = "anomalies"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.asset_id"), index=True)
    ts: Mapped[float] = mapped_column(Float)
    score: Mapped[Optional[float]] = mapped_column(Float, default=None)
    threshold: Mapped[Optional[float]] = mapped_column(Float, default=None)
    is_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    true_onset_ts: Mapped[Optional[float]] = mapped_column(Float, default=None)
    detection_delay: Mapped[Optional[float]] = mapped_column(Float, default=None)
    false_alarm_flag: Mapped[bool] = mapped_column(Boolean, default=False)


class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.asset_id"), index=True)
    ts: Mapped[float] = mapped_column(Float)
    fault_type: Mapped[str] = mapped_column(String(32))
    probability: Mapped[Optional[float]] = mapped_column(Float, default=None)
    severity_estimate: Mapped[Optional[float]] = mapped_column(Float, default=None)
    affected_signals_json: Mapped[dict] = mapped_column(JSON, default=dict)
    method: Mapped[str] = mapped_column(String(64), default="seed")
    model_version: Mapped[str] = mapped_column(String(32), default="seed-v1")


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.asset_id"), index=True)
    ts: Mapped[float] = mapped_column(Float)
    health_index: Mapped[Optional[float]] = mapped_column(Float, default=None)
    rul_estimate: Mapped[Optional[float]] = mapped_column(Float, default=None)
    rul_lower: Mapped[Optional[float]] = mapped_column(Float, default=None)
    rul_upper: Mapped[Optional[float]] = mapped_column(Float, default=None)
    confidence: Mapped[Optional[float]] = mapped_column(Float, default=None)
    model_version: Mapped[str] = mapped_column(String(32), default="seed-v1")


class MaintenanceEvent(Base):
    __tablename__ = "maintenance_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.asset_id"), index=True)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)
    performed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)
    action_type: Mapped[str] = mapped_column(String(32), default="preventive")
    cost: Mapped[Optional[float]] = mapped_column(Float, default=None)
    duration_h: Mapped[Optional[float]] = mapped_column(Float, default=None)
    resources_json: Mapped[dict] = mapped_column(JSON, default=dict)
    outcome: Mapped[Optional[str]] = mapped_column(String(32), default=None)


class MaintenancePlan(Base):
    __tablename__ = "maintenance_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    horizon_days: Mapped[int] = mapped_column(Integer)
    plan_json: Mapped[dict] = mapped_column(JSON, default=dict)
    objective_value: Mapped[Optional[float]] = mapped_column(Float, default=None)
    solver: Mapped[str] = mapped_column(String(32), default="scipy-milp")
    constraints_json: Mapped[dict] = mapped_column(JSON, default=dict)


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    config_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metrics_json: Mapped[dict] = mapped_column(JSON, default=dict)
    artifacts_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)