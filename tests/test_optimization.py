"""Phase 6 tests: criticality model + maintenance-schedule optimisation."""

import numpy as np
import pytest

from optimization import (
    AssetPlanningInput,
    SchedulerInput,
    criticality_report,
    do_nothing_policy,
    greedy_schedule,
    milp_schedule,
    p_fail_before,
    schedule_cost,
)


def mk_asset(aid, rul_p50, failure_cost=100_000.0,
             maintenance_cost=12_000.0):
    return AssetPlanningInput(
        asset_id=aid,
        rul_days={"p10": max(0.4, rul_p50 * 0.7),
                  "p50": rul_p50,
                  "p90": rul_p50 * 1.4},
        failure_cost=failure_cost,
        maintenance_cost=maintenance_cost)


# ---------------------------------------------------------------------------
# criticality
# ---------------------------------------------------------------------------


def test_p_fail_before_quantile_anchors_and_clamps():
    rul = {"p10": 5.0, "p50": 10.0, "p90": 20.0}
    assert p_fail_before(10.0, rul) == pytest.approx(0.5, abs=1e-9)
    assert p_fail_before(5.0, rul) == pytest.approx(0.10, abs=1e-9)
    assert p_fail_before(20.0, rul) == pytest.approx(0.90, abs=1e-9)
    # outside the anchors: clamped, monotone in horizon
    assert p_fail_before(0.1, rul) == p_fail_before(0.01, rul) >= 0.02
    assert p_fail_before(1000.0, rul) <= 0.98
    assert p_fail_before(7.0, rul) < p_fail_before(8.0, rul)
    assert p_fail_before(14.0, rul) > p_fail_before(12.0, rul)


def test_criticality_report_risk_and_classes():
    assets = [
        mk_asset("A", rul_p50=1.5, failure_cost=200_000.0),
        mk_asset("B", rul_p50=6.0, failure_cost=100_000.0),
        mk_asset("C", rul_p50=30.0, failure_cost=150_000.0),
        mk_asset("D", rul_p50=2.0, failure_cost=80_000.0),
        mk_asset("E", rul_p50=4.0, failure_cost=120_000.0),
        mk_asset("F", rul_p50=8.0, failure_cost=90_000.0),
    ]
    rep = criticality_report(assets, horizon_days=14.0)
    assert rep["horizon_days"] == 14.0
    rows = {r["asset_id"]: r for r in rep["assets"]}
    # A (RUL 1.5 d) is riskier than C (RUL 30 d)
    assert rows["A"]["risk"] > rows["C"]["risk"]
    assert rows["A"]["class"] == "A" and rows["C"]["class"] == "C"
    assert all(r["explanation"].startswith("risk ") for r in rep["assets"])
    # A/B/C all present across the fleet
    assert {r["class"] for r in rep["assets"]} == {"A", "B", "C"}


# ---------------------------------------------------------------------------
# scheduling
# ---------------------------------------------------------------------------


def small_input(capacity=2) -> SchedulerInput:
    return SchedulerInput(
        assets=[
            mk_asset("A1", rul_p50=2.0, failure_cost=200_000.0),
            mk_asset("A2", rul_p50=2.5, failure_cost=150_000.0),
            mk_asset("A3", rul_p50=3.5, failure_cost=120_000.0),
            mk_asset("A4", rul_p50=6.0, failure_cost=100_000.0),
            mk_asset("A5", rul_p50=9.0, failure_cost=90_000.0),
            mk_asset("A6", rul_p50=20.0, failure_cost=110_000.0),
        ],
        horizon_days=7,
        capacity_per_day=capacity,
        no_maintenance_days=[5],
    )


def test_schedule_cost_accounting():
    assets = small_input().assets
    # all maintained preventively on day 0 (all safe_day >= 1)
    all_planned = np.zeros(len(assets), dtype=int)
    rep = schedule_cost(assets, all_planned, 7)
    assert rep["planned"] == 6 and rep["reactive"] == 0 and rep["failures"] == 0
    assert rep["total_cost"] == pytest.approx(
        sum(a.maintenance_cost for a in assets), abs=1)
    # no maintenance: assets with RUL < 7 (A1..A4; A5 has RUL 9) fail
    none = np.full(len(assets), 7)
    rep2 = schedule_cost(assets, none, 7)
    assert rep2["failures"] == 4 and rep2["total_cost"] == pytest.approx(
        sum(a.failure_cost for a in assets[:4]), abs=1)


def test_milp_schedule_feasibility_and_dominance():
    inp = small_input(capacity=2)
    sol = milp_schedule(inp)
    greedy = greedy_schedule(inp)
    nothing = do_nothing_policy(inp)

    # capacity + one-action-per-asset constraints hold; assets whose RUL
    # exceeds the horizon may be optimally left unmaintained (that is a
    # valid, cheaper action, not a constraint violation)
    days = [d for d in sol["schedule"].values() if d is not None]
    assert len(days) <= len(inp.assets)
    skipped = [a.asset_id for a in inp.assets
               if sol["schedule"][a.asset_id] is None]
    for aid in skipped:
        assert float(next(a.rul_days["p50"] for a in inp.assets
                          if a.asset_id == aid)) >= inp.horizon_days
    from collections import Counter
    counts = Counter(days)
    assert max(counts.values()) <= inp.capacity_per_day
    assert 5 not in counts  # window day has no maintenance

    # MILP never worse than the baselines
    assert sol["objective"] <= greedy["objective"] + 1e-6
    assert sol["objective"] <= nothing["objective"] + 1e-6
    assert greedy["objective"] <= nothing["objective"] + 1e-6

    # every reactive/failure accounted for in the per-policy cost dict
    for p in (sol, greedy, nothing):
        c = p["cost"]
        assert c["planned"] + c["reactive"] + c["failures"] <= len(inp.assets)
        assert c["total_cost"] == pytest.approx(p["objective"], abs=0.5)


def test_milp_schedule_deterministic():
    a = milp_schedule(small_input())
    b = milp_schedule(small_input())
    assert a == b


def test_greedy_respects_windows_and_capacity():
    inp = small_input(capacity=1)
    sol = greedy_schedule(inp)
    days = [d for d in sol["schedule"].values() if d is not None]
    counts = dict(zip(*np.unique(days, return_counts=True)))
    assert max(counts.values()) <= 1
    assert 5 not in counts