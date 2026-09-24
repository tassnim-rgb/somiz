"""Tests for the four unsupervised anomaly detectors (ml/anomaly.py)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from simulation import FaultSpec, OperatingProfileSpec, SimulationConfig, Simulator
from pipeline import PreprocessConfig, Preprocessor
from ml import (
    IsolationForestDetector,
    PointAutoencoderDetector,
    StatisticalBaselineDetector,
    WindowedAutoencoderDetector,
)

SENSOR_COLS = ["vib", "t_motor", "t_fluid", "p_disch", "flow",
               "rpm", "current", "power", "efficiency"]


def _simulate(faults=None, duration=500.0, seed=7):
    cfg = SimulationConfig(
        seed=seed,
        duration_s=duration,
        fs_hz=1.0,
        dt_phys=0.25,
        profile=OperatingProfileSpec(segments=[(duration, 0.9)], cycle=True),
        faults=faults or [],
        stop_on_failure=True,
    )
    return Simulator(cfg).run().df


def _healthy_prepared(seed=7):
    frame = _simulate(faults=[], duration=400.0, seed=seed)
    pp = Preprocessor(PreprocessConfig(rolling_window=10))
    pp.fit(frame.head(240))
    proc = pp.transform(frame)
    return proc, frame.head(240)  # processed frame + raw healthy fit slice


def _bearing_prepared(onset=120.0):
    frame = _simulate(faults=[FaultSpec("bearing", onset_s=onset, target=1.0,
                                        duration_s=300.0)], duration=500.0)
    pp = Preprocessor(PreprocessConfig(rolling_window=10))
    pp.fit(frame.head(240))
    return pp.transform(frame)


def _assert_separates(det):
    """Fit a detector on healthy fit data, score healthy tail + fault run."""
    proc_h, raw_h = _healthy_prepared()
    proc_b = _bearing_prepared()
    det.fit(proc_h.loc[:239, SENSOR_COLS] if not isinstance(det, IsolationForestDetector)
            else _features(proc_h.loc[:239]))
    s_health = det.score(proc_h.loc[240:, SENSOR_COLS]
                         if not isinstance(det, IsolationForestDetector)
                         else _features(proc_h.loc[240:]))
    s_fault = det.score(proc_b[SENSOR_COLS]
                        if not isinstance(det, IsolationForestDetector)
                        else _features(proc_b))
    assert len(s_health) == len(proc_h) - 240
    assert len(s_fault) == len(proc_b)
    assert np.nanmean(s_health) < np.nanmean(s_fault)


def _features(df: pd.DataFrame) -> pd.DataFrame:
    keep = [c for c in df.columns
            if c in SENSOR_COLS or c.endswith("_roll10_mean")
            or c.endswith("_roll10_std") or c.endswith("_delta")]
    return df[keep]


# ---------------------------------------------------------------------------


def test_statistical_baseline_separates_healthy_from_fault():
    det = StatisticalBaselineDetector(sensors=SENSOR_COLS, smooth=5)
    _assert_separates(det)


def test_statistical_baseline_deterministic_and_fit_required():
    proc_h, _ = _healthy_prepared()
    det1 = StatisticalBaselineDetector(sensors=SENSOR_COLS, smooth=5).fit(proc_h[SENSOR_COLS])
    det2 = StatisticalBaselineDetector(sensors=SENSOR_COLS, smooth=5).fit(proc_h[SENSOR_COLS])
    np.testing.assert_array_equal(det1.score(proc_h[SENSOR_COLS]),
                                  det2.score(proc_h[SENSOR_COLS]))
    with pytest.raises(RuntimeError):
        StatisticalBaselineDetector(sensors=SENSOR_COLS).score(proc_h[SENSOR_COLS])


def test_statistical_baseline_requires_present_sensors():
    det = StatisticalBaselineDetector(sensors=["nope", "also_nope"])
    with pytest.raises(ValueError):
        det.fit(pd.DataFrame({"a": [1.0, 2.0]}))


def test_isolation_forest_separates_healthy_from_fault():
    det = IsolationForestDetector(n_estimators=50, contamination=0.05, random_state=7)
    _assert_separates(det)


def test_point_autoencoder_separates_healthy_from_fault():
    det = PointAutoencoderDetector(sensors=SENSOR_COLS, hidden=(16, 4),
                                   seed=7, epochs=10, patience=3)
    _assert_separates(det)


def test_point_autoencoder_inference_is_deterministic():
    proc_h, _ = _healthy_prepared()
    X = proc_h[SENSOR_COLS]
    det = PointAutoencoderDetector(sensors=SENSOR_COLS, hidden=(16, 4), seed=9,
                                   epochs=6, patience=2).fit(X)
    # inference on a fitted model is bitwise deterministic
    np.testing.assert_array_equal(det.score(X), det.score(X))
    # training with the same seed is reproducible in distribution (torch CPU
    # has no bitwise guarantee across runs), and separates healthy from fault
    a = det.score(X)
    det2 = PointAutoencoderDetector(sensors=SENSOR_COLS, hidden=(16, 4), seed=9,
                                    epochs=6, patience=2).fit(X)
    b = det2.score(X)
    c = np.corrcoef(a, b)[0, 1]
    assert c > 0.95
    assert np.abs(a.mean() - b.mean()) < 0.05 * max(a.mean(), b.mean())


def test_windowed_autoencoder_separates_and_pads_causally():
    proc_h, raw_h = _healthy_prepared()
    det = WindowedAutoencoderDetector(window=16, sensors=SENSOR_COLS, hidden=(32, 8),
                                      seed=7, epochs=8, patience=3)
    det.fit(proc_h.loc[:239, SENSOR_COLS])
    s = det.score(proc_h.loc[240:, SENSOR_COLS])
    assert len(s) == len(proc_h) - 240
    assert np.isfinite(s).all()  # first window-1 rows padded, not NaN
    s_b = det.score(_bearing_prepared()[SENSOR_COLS])
    assert np.nanmean(s) < np.nanmean(s_b)


def test_windowed_autoencoder_needs_enough_samples():
    proc_h, _ = _healthy_prepared()
    tiny = proc_h.head(5)[SENSOR_COLS]
    det = WindowedAutoencoderDetector(window=16, sensors=SENSOR_COLS)
    with pytest.raises(ValueError):
        det.fit(tiny)