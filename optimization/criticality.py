"""Asset criticality model: P(failure) x consequence -> risk, with classes.

MODEL ASSUMPTION (stated, never hidden): the probability of failure in a
planning horizon is derived from a RUL *distribution* (p10 / p50 / p90
quantiles, e.g. from the Phase 5 quantile GBM) by piecewise-linear
interpolation in quantile space, clamped to [0.02, 0.98]. The consequence
(cost of an unplanned failure) is a planning input, not a measured value.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np

# hard floors / caps for the failure-probability estimate
P_FLOOR = 0.02
P_CEIL = 0.98


@dataclass(frozen=True)
class AssetPlanningInput:
    """Planning-time description of one asset.

    ``rul_days`` holds quantile estimates of the remaining useful life in
    days (keys "p10", "p50", "p90"); ``failure_cost`` is the cost of an
    unplanned failure and ``maintenance_cost`` the cost of a planned
    preventive intervention. All SIMULATED / MODEL ASSUMPTION.
    """

    asset_id: str
    rul_days: Dict[str, float]
    failure_cost: float
    maintenance_cost: float


def p_fail_before(horizon_days: float, rul_days: Dict[str, float]) -> float:
    """P(RUL < horizon) from p10/p50/p90 quantile anchors.

    Piecewise-linear through (p10, 0.10), (p50, 0.50), (p90, 0.90) with
    linear extrapolation outside the anchors, everything clamped to
    [P_FLOOR, P_CEIL]. MODEL ASSUMPTION - a convenient, cheap stand-in
    for a full survival model.
    """
    anchors = sorted(
        (float(rul_days[k]), q)
        for k, q in (("p10", 0.10), ("p50", 0.50), ("p90", 0.90))
    )
    xs = [a[0] for a in anchors]
    ys = [a[1] for a in anchors]
    h = float(horizon_days)
    if xs[0] > xs[1]:  # degenerate / bad input guard
        return P_FLOOR
    if h < xs[0]:
        slope = (ys[1] - ys[0]) / max(xs[1] - xs[0], 1e-9)
        return float(np.clip(ys[0] + slope * (h - xs[0]), P_FLOOR, P_CEIL))
    if h > xs[-1]:
        slope = (ys[1] - ys[0]) / max(xs[1] - xs[0], 1e-9)
        return float(np.clip(ys[-1] + slope * (h - xs[-1]), P_FLOOR, P_CEIL))
    return float(np.clip(np.interp(h, xs, ys), P_FLOOR, P_CEIL))


def criticality_report(
    assets: List[AssetPlanningInput],
    horizon_days: float,
) -> Dict[str, object]:
    """Per-asset risk = P(fail before horizon) * failure cost, plus A/B/C
    classes from the fleet's terciles of risk (MODEL ASSUMPTION)."""
    rows = []
    for a in assets:
        p = p_fail_before(horizon_days, a.rul_days)
        risk = p * a.failure_cost
        rows.append({
            "asset_id": a.asset_id,
            "rul_p50_days": round(float(a.rul_days["p50"]), 2),
            "p_fail_by_horizon": round(p, 4),
            "failure_cost": round(float(a.failure_cost), 0),
            "maintenance_cost": round(float(a.maintenance_cost), 0),
            "risk": round(float(risk), 0),
        })
    # tercile class boundaries over the fleet
    risks = np.array([r["risk"] for r in rows])
    lo, hi = np.quantile(risks, [1.0 / 3.0, 2.0 / 3.0])
    for r, rk in zip(rows, risks):
        r["class"] = "A" if rk >= hi else ("B" if rk >= lo else "C")
        r["explanation"] = (
            f"risk {r['risk']:.0f} EUR = P(fail by day {horizon_days:.0f}) "
            f"({r['p_fail_by_horizon']:.2f}) x failure cost "
            f"({r['failure_cost']:.0f} EUR)")
    return {"horizon_days": horizon_days, "assets": rows}