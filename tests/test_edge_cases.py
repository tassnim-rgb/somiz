"""Phase 11 edge-case suite: degenerate inputs must fail loudly or be safe.

The point is honesty under pressure: a twin that silently returns garbage
for empty/constant/degenerate inputs is worse than one that raises a clear
error. Each test pins the CURRENT guaranteed behaviour (either a clean
ValueError/RuntimeError or finite outputs), so regressions surface.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from digital_twin import HealthIndex
from ml import IsolationForestDetector, StatisticalBaselineDetector
from optimization.scheduler import (
    SchedulerInput,
    do_nothing_policy,
    greedy_schedule,
    milp_schedule,
)
from pipeline import Preprocessor
from pipeline.features import rolling_features
from simulation import OperatingProfileSpec, SimulationConfig, Simulator


def _simulate(duration=300.0, seed=7):
    cfg = SimulationConfig(
        seed=seed,
        duration_s=duration,
        fs_hz=1.0,
        dt_phys=0.25,
        profile=OperatingProfileSpec(segments=[(duration, 0.9)], cycle=True),
        stop_on_failure=True,
    )
    return Simulator(cfg).run().df


# ---------------------------------------------------------------------------
# Simulator
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad", [0.0, -10.0])
def test_simulator_rejects_nonpositive_duration(bad):
    cfg = SimulationConfig(seed=1, duration_s=bad, fs_hz=1.0, dt_phys=0.25,
                           profile=OperatingProfileSpec(
                               segments=[(60, 0.9)], cycle=True))
    with pytest.raises(ValueError, match="duration_s"):
        Simulator(cfg)


def test_simulator_rejects_nonpositive_fs():
    cfg = SimulationConfig(seed=1, duration_s=300, fs_hz=0.0, dt_phys=0.25,
                           profile=OperatingProfileSpec(
                               segments=[(300, 0.9)], cycle=True))
    with pytest.raises(ValueError):
        Simulator(cfg)


def test_simulator_short_run_is_finite():
    df = _simulate(duration=8.0)
    assert len(df) >= 8
    for col in ["vib", "t_motor", "p_disch", "flow"]:
        assert np.isfinite(df[col]).all()


# ---------------------------------------------------------------------------
# Health index: constant columns and dropouts
# ---------------------------------------------------------------------------


def test_health_index_constant_column_is_uninformative():
    """A degenerate constant sensor must not blow up the index (sigma guard)."""
    frame = _simulate(duration=300.0)
    frame["efficiency"] = 0.5   # constant column inside sensor_weights
    hi = HealthIndex().fit(frame)
    # constant reference -> residual std near zero -> uninformative sigma
    assert hi._sigma["efficiency"] == pytest.approx(1.0)
    ev = hi.evaluate(frame)
    steady = ev[ev["hi_stage"] != "WARMUP"]
    assert np.isfinite(steady["hi"]).all()
    assert steady["hi"].between(0.0, 100.0).all()


def test_health_index_sustained_dropout_is_no_reading_not_fabricated():
    frame = _simulate(duration=300.0)
    hi = HealthIndex().fit(frame)
    idx = len(frame) // 2          # t >= warmup here
    # once the whole trailing 60-sample smoothing window is missing, the
    # index must refuse to fabricate a value
    frame.loc[idx: idx + 100, "flow"] = np.nan
    ev = hi.evaluate(frame)
    no_reading = ev[ev["hi_stage"] == "NO_READING"]
    block_len = 101
    # the refusal starts once a full smoothing window is missing and lasts
    # to the end of the dropout (trailing window semantics)
    assert len(no_reading) == block_len - hi.cfg.window + 1
    assert no_reading.index[0] == idx + hi.cfg.window - 1
    assert no_reading["hi"].isna().all()
    # the index resumes as soon as readings return
    tail = ev.loc[idx + 101:]
    assert tail["hi"].notna().all()


# ---------------------------------------------------------------------------
# Anomaly detectors
# ---------------------------------------------------------------------------


def test_baseline_detector_constant_frame_scores_zero():
    frame = pd.DataFrame({
        "vib": np.full(60, 0.42),
        "t_motor": np.full(60, 32.0),
    })
    det = StatisticalBaselineDetector(sensors=["vib", "t_motor"]).fit(frame)
    scores = det.score(frame)
    assert len(scores) == 60
    assert np.isfinite(scores).all()
    assert np.allclose(scores, 0.0)


def test_baseline_detector_all_nan_column_raises():
    frame = pd.DataFrame({"vib": [np.nan] * 10})
    with pytest.raises(ValueError, match="finite"):
        StatisticalBaselineDetector(sensors=["vib"]).fit(frame)


def test_baseline_detector_cannot_score_before_fit():
    det = StatisticalBaselineDetector(sensors=["vib"])
    with pytest.raises(RuntimeError):
        det.score(pd.DataFrame({"vib": [1.0, 2.0]}))


def test_isolation_forest_tiny_score_frame_is_finite():
    rng = np.random.default_rng(0)
    fit_frame = pd.DataFrame(rng.normal(size=(60, 4)), columns=list("abcd"))
    det = IsolationForestDetector(contamination=0.05,
                                  n_estimators=50).fit(fit_frame)
    tiny = pd.DataFrame(rng.normal(size=(6, 4)), columns=list("abcd"))
    scores = det.score(tiny)
    assert scores.shape == (6,)
    assert np.isfinite(scores).all()


# ---------------------------------------------------------------------------
# Maintenance scheduler: zero assets
# ---------------------------------------------------------------------------


def test_scheduler_zero_assets_returns_empty_plan():
    inp = SchedulerInput(assets=[], horizon_days=30)
    for plan in (milp_schedule(inp), greedy_schedule(inp),
                 do_nothing_policy(inp)):
        assert plan["schedule"] == {}
        assert plan["objective"] == 0.0
        assert plan["cost"]["total_cost"] == 0.0
        assert plan["cost"]["planned"] == 0
        assert plan["cost"]["failures"] == 0


# ---------------------------------------------------------------------------
# Preprocessing
# ---------------------------------------------------------------------------


def test_preprocessor_validate_empty_frame_does_not_crash():
    rep = Preprocessor().validate(pd.DataFrame())
    assert isinstance(rep.ok, bool)
    assert rep.ok is False            # missing required columns
    assert rep.n_rows == 0


def test_rolling_features_short_frame_returns_rows():
    df = pd.DataFrame({"t": np.arange(5.0),
                       "vib": [1.0, 2.0, 3.0, 2.0, 1.0]})
    out = rolling_features(df, ["vib"], window=10, shift=1)
    assert len(out) == len(df)
    assert np.isfinite(out["vib_roll10_mean"].iloc[-1])