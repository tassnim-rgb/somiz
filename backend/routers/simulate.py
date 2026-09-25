"""Simulation lab endpoint: run a short SIMULATED run on demand.

This powers the dashboard's "Laboratoire de simulation" tab. Everything
returned is produced by the Phase 2 physics twin right now; the health
index reference is the healthy twin of the same seed (commissioning
baseline model assumption). It never describes a real plant.
"""

from __future__ import annotations

import math
from typing import List, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from simulation import Simulator, SimulationConfig
from simulation.config import FaultSpec
from digital_twin import HealthIndex

router = APIRouter(prefix="/api/simulate", tags=["simulation-lab"])

SCENARIOS = {"healthy", "bearing", "leakage", "blockage"}
TARGETS = {"bearing": 1.0, "leakage": 0.8, "blockage": 0.7}


class SimulateRequest(BaseModel):
    scenario: Literal["healthy", "bearing", "leakage", "blockage"] = "healthy"
    seed: int = Field(default=42, ge=0, le=2**31 - 1)
    duration_s: float = Field(default=300, ge=240, le=3600,
                              allow_inf_nan=False,
                              description="minimum 240 s so a health-index "
                                          "reference can be fitted after the "
                                          "120 s warmup")
    stride: int = Field(default=0, ge=0, le=60, description="0 = auto")


class SimulateResponse(BaseModel):
    simulated: Literal[True] = True
    scenario: str
    seed: int
    duration_s: float
    n_samples: int
    stride: int
    warmup_s: float
    t: List[float]
    vib: List[float]
    t_motor: List[float]
    p_disch: List[float]
    flow: List[float]
    health_index: List[Optional[float]]
    fault_severity: List[float]
    dominant_fault: List[str]


def _run(scenario: str, seed: int, duration_s: float):
    cfg = SimulationConfig(seed=seed, duration_s=duration_s, fs_hz=1,
                           stop_on_failure=False)
    if scenario != "healthy":
        cfg.faults = [FaultSpec(scenario, onset_s=min(120.0, duration_s * 0.4),
                                target=TARGETS[scenario],
                                duration_s=duration_s * 0.6)]
    return Simulator(cfg).run().df


@router.post("", response_model=SimulateResponse)
def simulate(req: SimulateRequest):
    if req.scenario not in SCENARIOS:
        raise HTTPException(status_code=422, detail="unknown scenario")
    reference = _run("healthy", req.seed, req.duration_s)
    frame = _run(req.scenario, req.seed, req.duration_s)
    hi = HealthIndex().fit(reference)
    ev = hi.evaluate(frame)

    n = len(frame)
    stride = req.stride or max(1, int(n / 400))
    idx = list(range(0, n, stride))
    hi_vals = ev["hi"].to_numpy(dtype=float)
    hi_list: List[Optional[float]] = [
        None if math.isnan(float(hi_vals[i])) else round(float(hi_vals[i]), 3)
        for i in idx
    ]
    return SimulateResponse(
        scenario=req.scenario,
        seed=req.seed,
        duration_s=req.duration_s,
        n_samples=n,
        stride=stride,
        warmup_s=hi.cfg.warmup_s,
        t=[float(frame["t"].iloc[i]) for i in idx],
        vib=[float(frame["vib"].iloc[i]) for i in idx],
        t_motor=[float(frame["t_motor"].iloc[i]) for i in idx],
        p_disch=[float(frame["p_disch"].iloc[i]) for i in idx],
        flow=[float(frame["flow"].iloc[i]) for i in idx],
        health_index=hi_list,
        fault_severity=[float(frame["fault_severity"].iloc[i]) for i in idx],
        dominant_fault=[str(frame["dominant_fault"].iloc[i]) for i in idx],
    )