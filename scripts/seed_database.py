#!/usr/bin/env python
"""Seed the SOMIZ SQLite database with a deterministic SIMULATED demo
fleet (Phase 7 deliverable).

Creates one database file (data/somiz.db by default) containing:

  - 4 simulated pump assets (1 healthy, 3 with faults) + per-asset sensor
    catalog + full measurement series (900 s, NaN dropouts marked MISSING);
  - ground-truth faults, health-index predictions (Phase 4), SIMULATED
    diagnoses (ground-truth labelled), statistical anomaly flags;
  - a maintenance plan produced by the Phase 6 MILP scheduler + events;
  - experiment catalogue rows pointing at the committed result artefacts.

EVERYTHING SEEDED IS SIMULATED / MODEL ASSUMPTION. Rows produced from
simulator ground truth are labelled method='ground_truth_seed' and are
for dashboard/API demos only; live estimates from the Phase 5 models are
the documented replacement when the streaming path lands.

Usage:
  python scripts/seed_database.py [--seed 42] [--reset]
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
from sqlalchemy import select

from backend.database import Base, SessionLocal, engine
from backend.models import (
    Anomaly,
    Asset,
    Diagnosis,
    Experiment,
    Fault,
    MaintenanceEvent,
    MaintenancePlan,
    Measurement,
    Prediction,
    Sensor,
)
from digital_twin import HealthIndex
from ml.anomaly import StatisticalBaselineDetector
from ml.rul import build_rul_target
from optimization import (
    AssetPlanningInput,
    SchedulerInput,
    criticality_report,
    milp_schedule,
)
from simulation import Simulator, SimulationConfig
from simulation.config import FaultSpec

# Same tag set and display units as simulation.default_sensor_set() so the
# database catalog matches the frames that are seeded from it.
SENSOR_DEFS = [
    ("vib", "vibration", "mm/s", "vibration"),
    ("t_motor", "motor temperature", "°C", "thermal"),
    ("t_fluid", "fluid temperature", "°C", "thermal"),
    ("p_disch", "discharge pressure", "bar", "hydraulic"),
    ("flow", "flow rate", "m³/h", "hydraulic"),
    ("rpm", "shaft speed", "tr/min", "mechanical"),
    ("current", "motor current", "A", "electrical"),
    ("power", "motor power", "kW", "electrical"),
    ("efficiency", "pump efficiency", "%", "hydraulic"),
]
DURATION_S = 900.0
HI_STRIDE = 10
ANOM_STRIDE = 5
PLAN_MAINT_FRAC = 0.15


def simulate_asset(seed: int, scenario: str) -> pd.DataFrame:
    cfg = SimulationConfig(seed=seed, duration_s=DURATION_S, fs_hz=1,
                           stop_on_failure=False)
    if scenario != "healthy":
        onset, target, dur = {
            "bearing": (300.0, 1.0, 600.0),
            "leakage": (300.0, 0.8, 600.0),
            "blockage": (300.0, 0.7, 600.0),
        }[scenario]
        cfg.faults = [FaultSpec(scenario, onset_s=onset, target=target,
                                duration_s=dur)]
    return Simulator(cfg).run().df


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--reset", action="store_true",
                    help="drop existing tables first")
    args = ap.parse_args()

    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        if not args.reset and db.scalar(select(Asset).limit(1)) is not None:
            print("database already seeded (use --reset to rebuild)")
            return 1

        if args.reset:
            Base.metadata.drop_all(engine)
            Base.metadata.create_all(engine)

        # ------- 1. fleet: 1 healthy + 3 faulted assets (900 s) ----------
        scenarios = {"A00": "healthy", "A01": "bearing",
                     "A02": "leakage", "A03": "blockage"}
        frames = {aid: simulate_asset(args.seed + i, scen)
                  for i, (aid, scen) in enumerate(scenarios.items())}

        # healthy reference for the health index and anomaly detector
        healthy_frame = frames["A00"]

        # ------- 2. assets + sensors + measurements ----------------------
        for aid, scen in scenarios.items():
            f = frames[aid]
            db.add(Asset(
                asset_id=aid,
                asset_type="motor-driven-centrifugal-pump",
                name=f"pump {aid} ({scen})",
                description=("SIMULATED asset; scenario " + scen +
                             ". Ground truth from the physics twin."),
                params_json={"scenario": scen, "duration_s": DURATION_S},
                criticality_json={},
            ))
            for tag, name, unit, kind in SENSOR_DEFS:
                db.add(Sensor(asset_id=aid, tag=tag, name=name,
                              unit=unit, kind=kind))
            db.flush()  # materialise asset/sensor rows before lookups
            # measurement series with MISSING flags on telemetry dropouts
            for tag, name, unit, kind in SENSOR_DEFS:
                sensor = db.query(Sensor).filter_by(asset_id=aid, tag=tag).one()
                vals = f[tag].to_numpy(dtype=float)
                ts = f["t"].to_numpy(dtype=float)
                for t, v in zip(ts, vals):
                    db.add(Measurement(
                        asset_id=aid, sensor_id=sensor.id, ts=float(t),
                        value=None if np.isnan(v) else float(v),
                        quality_flag="MISSING" if np.isnan(v) else "OK"))

        # ------- 3. ground-truth faults ----------------------------------
        for aid, scen in scenarios.items():
            if scen == "healthy":
                continue
            f = frames[aid]
            onset = 300.0
            db.add(Fault(
                asset_id=aid, fault_type=scen, onset_ts=onset,
                severity=float(f["fault_severity"].max()),
                progression_params={"onset_s": onset,
                                    "target": {"bearing": 1.0, "leakage": 0.8,
                                               "blockage": 0.7}[scen]},
                ground_truth_state="simulated",
                notes="SIMULATED fault injected by the physics twin."))

        # ------- 4. health-index predictions + ground-truth diagnoses ----
        hi = HealthIndex().fit(healthy_frame)
        for aid, scen in scenarios.items():
            f = frames[aid]
            ev = hi.evaluate(f)
            t = f["t"].to_numpy(dtype=float)
            sev = f["fault_severity"].to_numpy(dtype=float)
            dom = f["dominant_fault"].to_numpy(dtype=object)
            rul = None
            if scen != "healthy":
                target = {"bearing": 1.0, "leakage": 0.8,
                          "blockage": 0.7}[scen]
                rul = build_rul_target(f, target)
            for i in range(0, len(f), HI_STRIDE):
                hi_v = ev["hi"].iloc[i]
                if np.isnan(hi_v):
                    continue  # WARMUP / NO_READING: no fabricated value
                db.add(Prediction(
                    asset_id=aid, ts=float(t[i]), health_index=float(hi_v),
                    rul_estimate=(float(rul[i]) if rul is not None else None),
                    model_version="seed-v1"))
                label = dom[i] if sev[i] >= 0.05 else "healthy"
                db.add(Diagnosis(
                    asset_id=aid, ts=float(t[i]), fault_type=str(label),
                    probability=1.0 if sev[i] >= 0.05 else None,
                    severity_estimate=float(sev[i]),
                    affected_signals_json={},
                    method="ground_truth_seed",
                    model_version="seed-v1"))

        # ------- 5. statistical anomaly flags ----------------------------
        det = StatisticalBaselineDetector(
            sensors=[d[0] for d in SENSOR_DEFS], smooth=15)
        det.fit(healthy_frame)
        threshold = 2.5
        for aid, scen in scenarios.items():
            f = frames[aid]
            t = f["t"].to_numpy(dtype=float)
            sev = f["fault_severity"].to_numpy(dtype=float)
            score = det.score(f)
            onset = 300.0 if scen != "healthy" else None
            detected_at = np.where(score >= threshold)[0]
            first_det = float(t[detected_at[0]]) if detected_at.size else None
            for i in range(0, len(f), ANOM_STRIDE):
                is_det = bool(score[i] >= threshold)
                db.add(Anomaly(
                    asset_id=aid, ts=float(t[i]),
                    score=round(float(score[i]), 5), threshold=threshold,
                    is_detected=is_det,
                    true_onset_ts=onset,
                    detection_delay=(round(first_det - onset, 1)
                                     if scen != "healthy" and first_det is not None
                                     else None),
                    false_alarm_flag=bool(is_det and (scen == "healthy"
                                                      or sev[i] < 0.05))))

        db.commit()

        # ------- 6. maintenance plan (Phase 6 optimizer, SIMULATED) ------
        plan_fleet = [
            AssetPlanningInput(asset_id="A00", rul_days={"p10": 21.0, "p50": 30.0,
                                                         "p90": 42.0},
                               failure_cost=180_000.0,
                               maintenance_cost=27_000.0),
            AssetPlanningInput(asset_id="A01", rul_days={"p10": 0.8, "p50": 1.6,
                                                         "p90": 3.0},
                               failure_cost=320_000.0,
                               maintenance_cost=48_000.0),
            AssetPlanningInput(asset_id="A02", rul_days={"p10": 1.5, "p50": 2.4,
                                                         "p90": 4.0},
                               failure_cost=240_000.0,
                               maintenance_cost=36_000.0),
            AssetPlanningInput(asset_id="A03", rul_days={"p10": 2.0, "p50": 3.0,
                                                         "p90": 5.0},
                               failure_cost=220_000.0,
                               maintenance_cost=33_000.0),
        ]
        plan_inp = SchedulerInput(assets=plan_fleet, horizon_days=14,
                                  capacity_per_day=2, no_maintenance_days=[5, 12])
        plan = milp_schedule(plan_inp)
        crit = criticality_report(plan_fleet, horizon_days=14.0)
        crit_by_id = {r["asset_id"]: r for r in crit["assets"]}

        plan_row = MaintenancePlan(
            horizon_days=14,
            plan_json=plan["schedule"],
            objective_value=float(plan["objective"]),
            solver="scipy-milp",
            constraints_json={"capacity_per_day": 2,
                              "no_maintenance_days": [5, 12]})
        db.add(plan_row)
        db.flush()

        now = datetime.now(UTC)
        for aid, day in plan["schedule"].items():
            if day is None:
                continue
            cost = crit_by_id[aid]["maintenance_cost"]
            db.add(MaintenanceEvent(
                asset_id=aid, scheduled_at=now + timedelta(days=int(day)),
                action_type="preventive", cost=cost, duration_h=4.0,
                resources_json={"crew": "2 technicians"}, outcome="planned"))

        # write the criticality into the assets table
        for aid, r in crit_by_id.items():
            asset = db.scalar(select(Asset).where(Asset.asset_id == aid))
            asset.criticality_json = r

        # ------- 7. experiment catalogue ---------------------------------
        for name, cfg, metrics, artifacts in [
            ("phase4-anomaly", {"phase": 4},
             "experiments/results/anomaly_comparison.json",
             "docs/HEALTH_INDEX.md"),
            ("phase5-diagnosis-rul", {"phase": 5},
             "experiments/results/diagnosis_rul_comparison.json",
             "docs/DIAGNOSIS_RUL.md"),
            ("phase6-optimization", {"phase": 6},
             "experiments/results/optimization_comparison.json",
             "docs/OPTIMIZATION_MAINTENANCE.md"),
        ]:
            db.add(Experiment(name=name, config_json=cfg,
                              metrics_json={"results_file": metrics},
                              artifacts_json={"docs": artifacts}))

        db.commit()

        counts = {
            "assets": db.query(Asset).count(),
            "measurements": db.query(Measurement).count(),
            "diagnoses": db.query(Diagnosis).count(),
            "predictions": db.query(Prediction).count(),
            "anomalies": db.query(Anomaly).count(),
            "maintenance_events": db.query(MaintenanceEvent).count(),
        }
        print("seeded:", counts)
        print(f"plan objective (MILP, SIMULATED): {plan['objective']:.0f} EUR")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())