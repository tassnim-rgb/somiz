"""Failure-mode catalogue and progression manager.

Each fault is a dimensionless progression factor d(t) in [0, 1] with an
onset time, a target severity and a shape. A ground-truth health stage is
derived from the worst progression: NORMAL -> EARLY -> MODERATE -> SEVERE ->
FAILURE.

The catalogue maps fault types to the physics keys consumed by
``physics.RotatingMachine.rhs``:
    bearing      -> friction + vibration growth
    overheating  -> reduced motor cooling
    leakage      -> internal recirculation, reduced net flow
    impeller     -> reduced flow and head
    blockage     -> reduced flow, raised pressure, raised vibration
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import Dict, List

from .config import FaultSpec, HealthStage

FAULT_TYPES = {
    "bearing": "usure roulement",
    "overheating": "surchauffe moteur",
    "leakage": "fuite / recirculation interne",
    "impeller": "usure roue (érosion)",
    "blockage": "obstruction partielle refoulement",
}

# optional coupling: which physics dict key each fault drives
FAULT_TO_PHYSICS = {
    "bearing": "bearing",
    "overheating": "overheating",
    "leakage": "leakage",
    "impeller": "impeller",
    "blockage": "blockage",
}


class FaultStageModel:
    """Maps the worst progression to a ground-truth health stage."""

    def __init__(self, thresholds: Dict[str, float]):
        # e.g. {"EARLY":0.05, "MODERATE":0.30, "SEVERE":0.60, "FAILURE":0.90}
        self._stages = [
            (HealthStage.FAILURE, thresholds.get("FAILURE", 0.90)),
            (HealthStage.SEVERE, thresholds.get("SEVERE", 0.60)),
            (HealthStage.MODERATE, thresholds.get("MODERATE", 0.30)),
            (HealthStage.EARLY, thresholds.get("EARLY", 0.05)),
        ]

    def stage(self, d: float) -> HealthStage:
        d = min(max(d, 0.0), 1.0)
        for stage, thr in self._stages:
            if d >= thr:
                return stage
        return HealthStage.NORMAL

    def worst_stage(self, progressions: Dict[str, float]) -> HealthStage:
        d = max(progressions.values()) if progressions else 0.0
        return self.stage(d)


class _Progressor:
    """Evaluates d(t) from a FaultSpec."""

    def __init__(self, spec: FaultSpec):
        self.spec = spec
        self.target = min(max(spec.target, 0.0), 1.0)

    def at(self, t: float, rng: np.random.Generator | None = None) -> float:
        spec = self.spec
        if t < spec.onset_s:
            return 0.0
        if spec.duration_s <= 0.0:
            return self.target
        t_on = t - spec.onset_s
        frac = min(1.0, t_on / spec.duration_s)
        if spec.shape == "step":
            return self.target if t_on >= 0 else 0.0
        if spec.shape == "exponential":
            k = 5.0 / spec.duration_s
            return self.target * (1.0 - np.exp(-k * t_on))
        return self.target * frac  # linear (default)


class FaultManager:
    """Owns the set of active faults and exposes their progression dict."""

    def __init__(self, fault_specs: List[FaultSpec], seed: int = 42):
        self._rng = np.random.default_rng(seed)
        self._specs: List[FaultSpec] = list(fault_specs)
        self._prog = [_Progressor(s) for s in self._specs]
        if len({(s.fault_type) for s in self._specs}) != len(self._specs):
            raise ValueError("duplicate fault type in one simulation")

    @property
    def specs(self) -> List[FaultSpec]:
        return list(self._specs)

    def progressions(self, t: float) -> Dict[str, float]:
        out: Dict[str, float] = {}
        for s, p in zip(self._specs, self._prog):
            out[s.fault_type] = float(p.at(t, self._rng))
        return out

    def physics_dict(self, t: float) -> Dict[str, float]:
        d = {}
        for ftype, val in self.progressions(t).items():
            key = FAULT_TO_PHYSICS.get(ftype)
            if key is not None:
                d[key] = val
        return d

    def worst(self, t: float) -> float:
        return max(self.progressions(t).values(), default=0.0)

    def active(self, t: float) -> List[FaultSpec]:
        return [s for s in self._specs if t >= s.onset_s]


def fault_from_spec(spec: FaultSpec) -> _Progressor:
    return _Progressor(spec)