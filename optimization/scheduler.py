"""Maintenance scheduling as a small MILP (scipy HiGHS), with baselines.

Problem (all inputs SIMULATED / MODEL ASSUMPTION):

  horizon H days, daily crew capacity per day. Each asset has a
  preventive-safe window: days d < d_safe(asset) where maintenance is
  cheap (planned). Replacing it later is reactive (cost = planned +
  failure cost). Assets never maintained pay an expected failure cost
  when their RUL estimate is shorter than the horizon.

Decision x[i,d] in {0,1} "maintain asset i on day d", plus a dummy day
d = H meaning "no maintenance". Objective: minimise total cost.
Constraints: exactly one action per asset; per-day crew capacity
(windows / no-maintenance days are capacity 0).

Solved with scipy.optimize.milp (HiGHS). CVXPY is a documented upgrade
path for larger / convex-differentiable variants (not installed; see
requirements.txt).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from .criticality import AssetPlanningInput


@dataclass
class SchedulerInput:
    assets: List[AssetPlanningInput]
    horizon_days: int
    capacity_per_day: int = 3
    # day indices (0-based) with no maintenance possible (e.g. weekends)
    no_maintenance_days: Optional[List[int]] = None

    def safe_day(self, asset: AssetPlanningInput) -> int:
        """Latest day a planned intervention is still preventive (0-based).

        day d is 'early enough' while d < floor(p50 RUL)."""
        return max(0, int(np.floor(float(asset.rul_days["p50"]))))


def _action_cost_matrix(inp: SchedulerInput) -> np.ndarray:
    """c[i, d] for d in 0..H-1 plus dummy day H = 'no maintenance'."""
    H = inp.horizon_days
    n = len(inp.assets)
    c = np.zeros((n, H + 1))
    for i, a in enumerate(inp.assets):
        safe = inp.safe_day(a)
        for d in range(H):
            if d < safe:
                c[i, d] = a.maintenance_cost          # planned, cheap
            else:
                c[i, d] = a.maintenance_cost + a.failure_cost  # reactive
        # dummy day H: leave unmaintained
        c[i, H] = a.failure_cost if float(a.rul_days["p50"]) < H else 0.0
    return c


def _milp_solution(inp: SchedulerInput, c: np.ndarray) -> Dict[str, object]:
    H = inp.horizon_days
    n = len(inp.assets)
    nvar = n * (H + 1)
    cflat = c.reshape(-1)

    rows = []
    lo, hi = [], []
    # exactly one action per asset
    for i in range(n):
        row = np.zeros(nvar)
        row[i * (H + 1): (i + 1) * (H + 1)] = 1.0
        rows.append(row)
        lo.append(1.0)
        hi.append(1.0)
    # daily capacity (window days have capacity 0)
    for d in range(H):
        row = np.zeros(nvar)
        row[d:: H + 1] = 1.0  # every asset's column d
        cap = 0.0 if (inp.no_maintenance_days and d in inp.no_maintenance_days) \
            else float(inp.capacity_per_day)
        rows.append(row)
        lo.append(0.0)
        hi.append(cap)
    A = np.vstack(rows)
    res = milp(
        c=cflat,
        constraints=LinearConstraint(A, np.array(lo), np.array(hi)),
        integrality=np.ones(nvar),
        bounds=Bounds(np.zeros(nvar), np.ones(nvar)),
    )
    if res.status != 0:
        raise RuntimeError(f"milp failed: {res.message}")
    x = np.rint(res.x).astype(int).reshape(n, H + 1)
    action = np.argmax(x, axis=1)  # the single chosen action per asset
    return {
        "action": action,           # day index, or H = no maintenance
        "x": x,
        "objective": float(res.fun),
        "status": res.message,
    }


def schedule_cost(
    assets: List[AssetPlanningInput],
    action: np.ndarray,            # per asset: day or H ('no maintenance')
    horizon_days: int,
) -> Dict[str, float]:
    """Cost of a concrete schedule, also used as the 'reality check'.

    NOTE (MODEL ASSUMPTION): in this twin the evaluation uses the same
    RUL estimates that drove the plan, so plan and reality coincide.
    Robustness of the schedule to RUL estimation error is explicitly a
    Phase 9 research item, not claimed here.
    """
    H = horizon_days
    planned = reactive = failures = 0
    cost = 0.0
    for i, a in enumerate(assets):
        d = int(action[i])
        safe = max(0, int(np.floor(float(a.rul_days["p50"]))))
        if d == H:  # no maintenance
            if float(a.rul_days["p50"]) < H:
                cost += a.failure_cost
                failures += 1
        elif d < safe:
            cost += a.maintenance_cost
            planned += 1
        else:
            cost += a.maintenance_cost + a.failure_cost
            reactive += 1
    return {
        "total_cost": round(float(cost), 0),
        "planned": planned,
        "reactive": reactive,
        "failures": failures,
    }


def milp_schedule(inp: SchedulerInput) -> Dict[str, object]:
    """Optimal (MILP) schedule."""
    if not inp.assets:
        # degenerate but valid input: nothing to maintain, zero cost
        return {
            "policy": "milp",
            "objective": 0.0,
            "schedule": {},
            "cost": {"total_cost": 0.0, "planned": 0,
                     "reactive": 0, "failures": 0},
        }
    c = _action_cost_matrix(inp)
    sol = _milp_solution(inp, c)
    action = sol["action"]
    breakdown = schedule_cost(inp.assets, action, inp.horizon_days)
    return {
        "policy": "milp",
        "objective": round(sol["objective"], 0),
        "schedule": {a.asset_id: (int(d) if d < inp.horizon_days else None)
                     for a, d in zip(inp.assets, action)},
        "cost": breakdown,
    }


def greedy_schedule(inp: SchedulerInput) -> Dict[str, object]:
    """Baseline: maintain assets in risk order (highest first), each on the
    earliest day whose capacity is free, preventive window preferred."""
    from .criticality import criticality_report, p_fail_before

    report = criticality_report(inp.assets, inp.horizon_days)
    ordered = sorted(report["assets"], key=lambda r: -r["risk"])
    by_id = {a.asset_id: a for a in inp.assets}
    action = {a.asset_id: inp.horizon_days for a in inp.assets}  # default: none
    used = {d: 0 for d in range(inp.horizon_days)}

    for r in ordered:
        a = by_id[r["asset_id"]]
        safe = inp.safe_day(a)
        # earliest free day inside the preventive window
        choice = None
        for d in range(0, min(safe, inp.horizon_days)):
            if (inp.no_maintenance_days and d in inp.no_maintenance_days):
                continue
            if used[d] < inp.capacity_per_day:
                choice = d
                break
        if choice is None:  # try any day (reactive)
            for d in range(inp.horizon_days):
                if (inp.no_maintenance_days and d in inp.no_maintenance_days):
                    continue
                if used[d] < inp.capacity_per_day:
                    choice = d
                    break
        if choice is not None:
            action[a.asset_id] = choice
            used[choice] += 1
    arr = np.array([action[a.asset_id] for a in inp.assets])
    return {
        "policy": "greedy",
        "objective": schedule_cost(inp.assets, arr, inp.horizon_days)["total_cost"],
        "schedule": {a.asset_id: (int(d) if d < inp.horizon_days else None)
                     for a, d in zip(inp.assets, arr)},
        "cost": schedule_cost(inp.assets, arr, inp.horizon_days),
    }


def do_nothing_policy(inp: SchedulerInput) -> Dict[str, object]:
    """Baseline: no preventive action; pay every failure inside the horizon."""
    arr = np.full(len(inp.assets), inp.horizon_days)
    return {
        "policy": "do_nothing",
        "objective": schedule_cost(inp.assets, arr, inp.horizon_days)["total_cost"],
        "schedule": {a.asset_id: None for a in inp.assets},
        "cost": schedule_cost(inp.assets, arr, inp.horizon_days),
    }