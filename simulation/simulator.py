"""Simulator: orchestrates the physics model, operating regime, fault
progression, sensor model and ground-truth health bookkeeping into a
reproducible multivariate time series.

Everything produced here is SIMULATED data. Ground-truth columns
(``health_stage``, ``fault_severity``, ``dominant_fault`` and per-fault
progressions) are recorded for evaluation of anomaly-detection and
diagnosis models; they would not exist in real telemetry.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from .config import (
    HealthStage,
    SensorAnomaly,
    SensorConfig,
    SimulationConfig,
    default_sensor_set,
)
from .faults import FaultManager, FaultStageModel
from .physics import RotatingMachine
from .regimes import OperatingProfile, profile_from_spec
from .sensors import SensorModel


@dataclass
class MeasurementFrame:
    """A simulated run: data frame + provenance metadata.

    ``df`` columns: ``t`` (s), one column per sensor tag, and ground truth:
    ``health_stage``, ``fault_severity``, ``dominant_fault``, plus
    ``d_<fault_type>`` progression columns and ``u`` (load demand).
    ``meta`` holds the full config snapshot, fault timeline and seed, so any
    row of data can be traced back to its generating assumptions.
    """

    df: pd.DataFrame
    meta: Dict[str, Any]

    def to_csv(self, path: str, **kwargs) -> str:
        self.df.to_csv(path, index=False, **kwargs)
        return path

    def to_parquet(self, path: str, **kwargs) -> str:
        self.df.to_parquet(path, index=False, **kwargs)
        return path

    @property
    def n_samples(self) -> int:
        return len(self.df)


class Simulator:
    """Runs a SimulationConfig end-to-end."""

    def __init__(self, config: SimulationConfig):
        errs = config.validate()
        if errs:
            raise ValueError("invalid SimulationConfig: " + "; ".join(errs))
        self.cfg = config
        self.rng = np.random.default_rng(config.seed)
        self.machine = RotatingMachine(config.machine)
        self.profile = profile_from_spec(config.profile)
        self.faults = FaultManager(config.faults, seed=config.seed)
        self.stages = FaultStageModel(config.fault_stage_thresholds)
        sensors = config.sensors or default_sensor_set()
        self.sensor_model = SensorModel(sensors, config.sensor_anomalies, seed=config.seed)
        self.sensors = sensors
        self._stuck = self.sensor_model.stuck_holders()

    # ------------------------------------------------------------------
    def run(self) -> MeasurementFrame:
        cfg = self.cfg
        fs = cfg.fs_hz
        dt = cfg.dt_phys
        n_samples = int(round(cfg.duration_s * fs)) + 1

        x = self.machine.x0()
        t = 0.0
        stopped_at: Optional[float] = None
        rows: List[Dict[str, Any]] = []

        for i in range(n_samples):
            t_samp = i / fs

            # advance physics from previous sample to this one
            while t < t_samp - 1e-9:
                step = min(dt, t_samp - t)
                u = self._demand(t, stopped_at)
                d = self.faults.physics_dict(t)
                x = self.machine.step_rk4(x, u, d, step)
                t += step

            u = self._demand(t_samp, stopped_at)
            d_phys = self.faults.physics_dict(t_samp)
            raw = self.machine.outputs(x, u, d_phys)

            # sensor corruption + stateful stuck anomalies
            obs = self.sensor_model.corrupt(raw, t_samp)
            for tag, holder in self._stuck.items():
                anom = next((a for a in cfg.sensor_anomalies
                             if a.sensor_tag == tag and a.kind == "stuck"), None)
                if anom is not None and tag in obs:
                    obs[tag] = holder.apply(obs[tag], t_samp, anom)

            # ground truth
            prog = self.faults.progressions(t_samp)
            stage = self.stages.stage(self.faults.worst(t_samp))
            dom = (max(prog, key=prog.get)
                   if prog and max(prog.values()) > 0.0 else "")

            row: Dict[str, Any] = {"t": round(t_samp, 6)}
            for s in self.sensors:
                row[s.tag] = obs.get(s.tag, float("nan"))
            row.update({
                "health_stage": stage.value,
                "fault_severity": float(max(prog.values(), default=0.0)),
                "dominant_fault": dom,
                "u": float(u),
            })
            for k, v in sorted(prog.items()):
                row[f"d_{k}"] = float(v)
            rows.append(row)

            # protective stop on failure (model assumption, see docs)
            if cfg.stop_on_failure and stopped_at is None and self.faults.worst(t_samp) >= 1.0:
                stopped_at = t_samp

        df = pd.DataFrame(rows)

        meta = {
            "simulated": True,
            "model": "rotating-machine-lumped-v1",
            "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "seed": cfg.seed,
            "duration_s": cfg.duration_s,
            "fs_hz": fs,
            "n_samples": n_samples,
            "fault_timeline": [
                {"fault_type": f.fault_type, "onset_s": f.onset_s,
                 "target": f.target, "duration_s": f.duration_s, "shape": f.shape,
                 "label": f.label or f.fault_type}
                for f in self.faults.specs
            ],
            "sensor_anomalies": [a.__dict__ for a in cfg.sensor_anomalies],
            "config": cfg.to_dict(),
            "legend": {
                "health_stage": [s.value for s in HealthStage],
                "fault_severity": "worst progression d in [0,1]; >=0.9 = FAILURE",
                "dominant_fault": "fault type with maximal progression at t",
                "d_<type>": "progression 0..1 of each configured fault",
                "stages": dict(cfg.fault_stage_thresholds),
            },
        }
        return MeasurementFrame(df=df, meta=meta)

    # ------------------------------------------------------------------
    def _demand(self, t: float, stopped_at: Optional[float]) -> float:
        if stopped_at is not None and t >= stopped_at:
            return 0.0
        return self.profile.u_at(t)

    def describe(self) -> str:
        """Short human summary of the configuration (for logs/reports)."""
        faults = ", ".join(f"{f.fault_type}@{f.onset_s}s->{f.target}" for f in self.faults.specs) or "none"
        return (
            f"Simulator(seed={self.cfg.seed}, T={self.cfg.duration_s}s, fs={self.cfg.fs_hz}Hz, "
            f"profile_segments={len(self.profile.segments)}, faults=[{faults}])"
        )