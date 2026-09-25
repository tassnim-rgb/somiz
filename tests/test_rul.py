"""Phase 5 tests: RUL targets, classical/temporal models, uncertainty."""

import numpy as np
import pandas as pd
import pytest

from simulation import Simulator, SimulationConfig
from simulation.config import FaultSpec
from ml.rul import (
    DEFAULT_CAP_S,
    QuantileGradientBoostingRUL,
    RidgeRUL,
    WindowMLPRegressor,
    build_rul_target,
    evaluate_rul,
    interval_coverage,
)


def run_frame(seed: int, duration: float = 300, faults=None) -> pd.DataFrame:
    cfg = SimulationConfig(seed=seed, duration_s=duration, fs_hz=1,
                           faults=faults or [], stop_on_failure=False)
    return Simulator(cfg).run().df


# ---------------------------------------------------------------------------
# target construction
# ---------------------------------------------------------------------------


def test_rul_target_shape_and_monotonic():
    frame = run_frame(1, faults=[
        FaultSpec("impeller", onset_s=50, target=0.7, duration_s=160)])
    rul = build_rul_target(frame, target=0.7)
    assert len(rul) == len(frame)
    assert rul.min() >= 0.0 and rul.max() <= DEFAULT_CAP_S
    # non-increasing in time (tolerance for float noise)
    assert np.all(np.diff(rul) <= 1e-6)
    # threshold 0.665 crossed on the linear ramp 50..210 s -> t ~ 202 s
    t_cross_approx = 50 + (0.665 / 0.7) * 160
    assert rul[0] == pytest.approx(t_cross_approx, abs=3.0)
    # RUL reaches zero at / after the crossing
    idx_zero = int(np.argmax(rul <= 1.0))
    assert frame["t"].iloc[idx_zero] >= t_cross_approx - 1.0
    assert rul[-1] <= 1.0


def test_rul_target_censored_flat_cap():
    frame = run_frame(2, faults=[
        FaultSpec("leakage", onset_s=50, target=0.8, duration_s=160)])
    # threshold_frac=2.0 -> threshold exceeds any reachable severity: censored
    rul = build_rul_target(frame, target=0.8, threshold_frac=2.0)
    assert np.all(rul == DEFAULT_CAP_S)


def test_evaluate_rul_and_coverage():
    y = np.array([100.0, 90.0, 80.0])
    p = np.array([95.0, 92.0, 85.0])
    rep = evaluate_rul(y, p)
    assert set(rep) == {"mae_s", "rmse_s", "mae_min", "n"}
    assert rep["mae_s"] == pytest.approx(4.0, abs=1e-9)
    assert interval_coverage(y, np.array([0.0, 0.0, 0.0]),
                             np.array([500.0, 500.0, 500.0])) == 1.0


# ---------------------------------------------------------------------------
# models (small synthetic, fast)
# ---------------------------------------------------------------------------


def _synthetic_rul_frac(seed=0, n=400):
    """Feature = remaining-life fraction; RUL = 1000 * fraction + noise.

    Rows are independent (no time coupling) and the feature distribution is
    the same in train and test, so the quantile model is doing interpolation
    rather than extrapolation - a fair check of its interval properties.
    """
    rng = np.random.default_rng(seed)
    frac = rng.random(n)
    X = pd.DataFrame({"frac": frac, "noise": rng.normal(0, 3, n)})
    y = pd.Series(1000.0 * frac + rng.normal(0, 25, n))
    return X, y


def test_quantile_gbm_intervals_hold():
    X, y = _synthetic_rul_frac()
    cut = int(len(X) * 0.7)
    q = QuantileGradientBoostingRUL(n_estimators=60, max_depth=3).fit(
        X.iloc[:cut], y.iloc[:cut])
    lo, med, hi = q.predict(X.iloc[cut:])
    y_te = y.iloc[cut:].to_numpy()
    cov = interval_coverage(y_te, lo, hi)
    assert cov >= 0.6
    assert evaluate_rul(y_te, med)["mae_s"] < 150.0


def test_window_mlp_learns_trend():
    rng = np.random.default_rng(1)
    n = 260
    t = np.arange(n, dtype=float)
    trend = 200.0 - t                     # ramps to 0 at the end
    sens = trend + rng.normal(0, 5, n)
    frame = pd.DataFrame({"t": t, "s1": sens, "s2": rng.normal(0, 1, n)})

    model = WindowMLPRegressor(window=24, sensors=["s1", "s2"], stride=3,
                               cap_s=200.0, epochs=40, batch=64, seed=0)
    model.fit(frame, np.clip(trend, 0, 200.0))
    pred = model.predict(frame)
    idx = np.arange(23, n, 3)
    mae = float(np.mean(np.abs(pred - np.clip(trend, 0, 200.0)[idx])))
    # constant baseline MAE is ~50; a trend-learner must do clearly better
    assert mae < 40.0


def test_window_mlp_device_resolution():
    import torch
    m = WindowMLPRegressor(window=8, sensors=["s1"], device="auto")
    expected = "cuda" if torch.cuda.is_available() else "cpu"
    assert m._device.type == expected
    m2 = WindowMLPRegressor(window=8, sensors=["s1"], device="cpu")
    assert m2._device.type == "cpu"
    with pytest.raises(ValueError):
        WindowMLPRegressor(window=8, sensors=["s1"], device="bogus")
    if not torch.cuda.is_available():
        # explicit cuda on a CUDA-less box must fail loudly, not half-run
        with pytest.raises(ValueError):
            WindowMLPRegressor(window=8, sensors=["s1"], device="cuda")


def test_ridge_rul_fit_predict():
    rng = np.random.default_rng(3)
    X = pd.DataFrame({
        "trend": np.linspace(0, 100, 120) + rng.normal(0, 3, 120),
        "noise": rng.normal(0, 5, 120),
    })
    y = 1000.0 - 8.0 * X["trend"].to_numpy()
    r = RidgeRUL().fit(X, y)
    rep = evaluate_rul(y, r.predict(X))
    assert rep["n"] == 120
    assert rep["rmse_s"] >= 0  # smoke: fits and scores without error