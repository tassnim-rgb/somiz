#!/usr/bin/env python
"""Maintenance-optimisation experiment (Phase 6 deliverable).

Builds a deterministic *planning* scenario (18 assets, 14-day horizon,
crew capacity scenarios, weekend window) and compares:

  - MILP schedule   (scipy.optimize.milp, HiGHS; the decision engine)
  - greedy baseline (maintain in criticality order, earliest free day)
  - do-nothing baseline (pay every in-horizon failure)

plus publication of the criticality report (risk = P(fail by horizon) x
failure cost; A/B/C classes).

ALL INPUTS ARE SIMULATED / MODEL ASSUMPTION: the RUL distributions in
days are planning inputs built from the scenario semantics of the twin
(not measured in any plant), and the 'reality check' uses the same
estimates that drove the plan (robustness of the schedule to RUL error
is Phase 9 research, not claimed here).

Results -> experiments/results/optimization_comparison.json

Usage:
  python scripts/run_optimization_experiment.py [--seed 42]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from optimization import (
    AssetPlanningInput,
    SchedulerInput,
    criticality_report,
    do_nothing_policy,
    greedy_schedule,
    milp_schedule,
)

HORIZON_DAYS = 14
WINDOW_DAYS = [5, 12]  # modelled weekend: no maintenance possible
MAINT_FRAC = 0.15      # planned maintenance = 15 % of failure cost (assumption)


def build_fleet(seed: int, n: int = 18) -> list:
    rng = np.random.default_rng(seed)
    assets = []
    for i in range(n):
        # planning RUL in days; a spread from near-end-of-life to safe
        rul_p50 = float(rng.uniform(1.2, 34.0))
        # "mission critical" tag gives the fleet its consequence spread
        critical = (i % 4 == 0)
        failure_cost = float(rng.uniform(60_000.0, 260_000.0)) * (2.5 if critical else 1.0)
        assets.append(AssetPlanningInput(
            asset_id=f"P{i:02d}",
            rul_days={"p10": max(0.5, rul_p50 * 0.7),
                      "p50": rul_p50,
                      "p90": rul_p50 * 1.5},
            failure_cost=failure_cost,
            maintenance_cost=failure_cost * MAINT_FRAC,
        ))
    return assets


def run_capacity(inp: SchedulerInput) -> dict:
    out = {"milp": milp_schedule(inp),
           "greedy": greedy_schedule(inp),
           "do_nothing": do_nothing_policy(inp)}
    m = out["milp"]["objective"]
    for k in ("greedy", "do_nothing"):
        out[f"milp_vs_{k}_saving_pct"] = round(
            100.0 * (out[k]["objective"] - m) / max(out[k]["objective"], 1.0), 2)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    t0 = time.time()

    fleet = build_fleet(args.seed)
    crit = criticality_report(fleet, horizon_days=HORIZON_DAYS)

    scenarios = {}
    for cap in (2, 3, 5):
        inp = SchedulerInput(assets=fleet, horizon_days=HORIZON_DAYS,
                             capacity_per_day=cap,
                             no_maintenance_days=WINDOW_DAYS)
        scenarios[f"capacity_{cap}"] = run_capacity(inp)

    base = scenarios["capacity_3"]
    results = {
        "experiment": "optimization-maintenance",
        "phase": 6,
        "seed": args.seed,
        "horizon_days": HORIZON_DAYS,
        "no_maintenance_days": WINDOW_DAYS,
        "n_assets": len(fleet),
        "macro_assumptions": [
            "RUL distributions (days, p10/p50/p90) are SIMULATED planning "
            "inputs, not plant measurements",
            "planned maintenance cost = 15 % of failure cost (MODEL "
            "ASSUMPTION)",
            "reality check uses the same RUL estimates that drove the plan; "
            "schedule robustness to RUL error is Phase 9 research",
            "CVXPY is the documented upgrade path for larger convex "
            "formulations; not installed (see requirements.txt)",
        ],
        "criticality": crit,
        "scenarios": scenarios,
        "headline": {
            "capacity": 3,
            "milp_cost": base["milp"]["cost"]["total_cost"],
            "greedy_cost": base["greedy"]["cost"]["total_cost"],
            "do_nothing_cost": base["do_nothing"]["cost"]["total_cost"],
            "milp_vs_greedy_saving_pct": base["milp_vs_greedy_saving_pct"],
            "milp_vs_do_nothing_saving_pct": base["milp_vs_do_nothing_saving_pct"],
            "failures_milp": base["milp"]["cost"]["failures"],
            "failures_greedy": base["greedy"]["cost"]["failures"],
            "failures_do_nothing": base["do_nothing"]["cost"]["failures"],
        },
        "solver": "scipy.optimize.milp (HiGHS)",
        "elapsed_s": round(time.time() - t0, 2),
    }
    out = Path("experiments/results/optimization_comparison.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")

    h = results["headline"]
    print(f"[optimization] capacity 3: milp {h['milp_cost']:.0f} EUR  "
          f"greedy {h['greedy_cost']:.0f}  do-nothing {h['do_nothing_cost']:.0f}")
    print(f"[optimization] saving vs greedy {h['milp_vs_greedy_saving_pct']}%  "
          f"vs do-nothing {h['milp_vs_do_nothing_saving_pct']}%")
    print(f"[optimization] results json: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())