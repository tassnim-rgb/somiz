"""Sensor-model tests: noise, drift, missing, outliers, stuck windows, clamp."""

import numpy as np
import pytest

from simulation.config import SensorAnomaly, SensorConfig
from simulation.sensors import SensorModel, StuckHolder


def _vib() -> SensorConfig:
    return SensorConfig(tag="vib", name="Vibration", source="vibration_rms",
                        unit="mm/s", noise_std=0.05, noise_rel=0.01,
                        drift_rate=0.0, missing_p=0.0, outlier_p=0.0)


def test_noise_changes_values_but_stays_close():
    sm = SensorModel([_vib()], [], seed=1)
    vals = [sm.corrupt({"vibration_rms": 5.0}, t=0)["vib"] for _ in range(500)]
    vals = np.array(vals)
    assert np.all(np.isfinite(vals))
    assert abs(vals.mean() - 5.0) < 0.1          # unbiased
    assert vals.std() > 0.0


def test_drift_is_linear_in_time():
    s = _vib()
    s.drift_rate = 0.01
    sm = SensorModel([s], [], seed=2)
    v100 = sm.corrupt({"vibration_rms": 5.0}, t=100)["vib"]
    v200 = sm.corrupt({"vibration_rms": 5.0}, t=200)["vib"]
    assert v200 - v100 == pytest.approx(1.0, abs=0.5)


def test_missing_produces_nan():
    s = _vib()
    s.missing_p = 0.5
    sm = SensorModel([s], [], seed=3)
    vals = [sm.corrupt({"vibration_rms": 5.0}, t=0)["vib"] for _ in range(200)]
    nan_count = sum(1 for v in vals if np.isnan(v))
    assert nan_count > 0 and nan_count < 200


def test_outlier_spikes_present():
    s = _vib()
    s.outlier_p = 0.05
    s.noise_std = 0.0
    s.noise_rel = 0.0
    sm = SensorModel([s], [], seed=4)
    vals = [sm.corrupt({"vibration_rms": 5.0}, t=0)["vib"] for _ in range(1000)]
    big = [v for v in vals if abs(v - 5.0) > 1.0]
    assert len(big) > 0


def test_clamp_to_bounds():
    s = _vib()
    s.lower, s.upper = 0.0, 10.0
    sm = SensorModel([s], [], seed=5)
    v = sm.corrupt({"vibration_rms": 50.0}, t=0)["vib"]
    assert 0.0 <= v <= 10.0


def test_stateless_anomaly_drift_blows_signal_up():
    s = _vib()
    a = SensorAnomaly(sensor_tag="vib", kind="drift", onset_s=100, duration_s=100, magnitude=1.0)
    sm = SensorModel([s], [a], seed=6)
    before = sm.corrupt({"vibration_rms": 5.0}, t=50)["vib"]
    during = sm.corrupt({"vibration_rms": 5.0}, t=190)["vib"]
    assert abs(before - 5.0) < 0.5              # unaffected before onset
    assert during > 5.5                          # drifting up inside window


def test_noise_burst_in_window():
    s = _vib()
    s.noise_std = 0.0   # isolate the burst
    a = SensorAnomaly(sensor_tag="vib", kind="noise_burst", onset_s=10, duration_s=20, magnitude=5.0)
    sm = SensorModel([s], [a], seed=7)
    vals = [sm.corrupt({"vibration_rms": 5.0}, t=20)["vib"] for _ in range(100)]
    assert np.std(vals) > 1.0  # much noisier than baseline (0.05)


def test_stuck_holds_value_then_releases():
    s = _vib()
    a = SensorAnomaly(sensor_tag="vib", kind="stuck", onset_s=100, duration_s=50)
    holder = StuckHolder(s)
    prev = None
    stale = 0
    for t in range(90, 170):
        v = 5.0 + 0.1 * (t - 90)  # underlying signal rising
        v = holder.apply(v, float(t), a)
        if 100 <= t < 150:
            if prev is not None and v != prev:
                stale += 1
            prev = v
        if t >= 150:
            assert v == pytest.approx(5.0 + 0.1 * (t - 90), abs=1e-6)  # released
    assert stale == 0  # strictly frozen inside window


def test_stuck_holder_reset():
    s = _vib()
    a = SensorAnomaly(sensor_tag="vib", kind="stuck", onset_s=100, duration_s=10)
    h = StuckHolder(s)
    h.apply(1.0, 105, a)
    assert h.apply(9.0, 108, a) == 1.0
    h.reset()
    assert h.apply(9.0, 108, a) == 9.0


def test_stuck_anomaly_unknown_sensor_rejected():
    sm = SensorModel([_vib()],
                     [SensorAnomaly(sensor_tag="nope", kind="stuck")], seed=8)
    with pytest.raises(ValueError):
        sm.stuck_holders()


def test_empty_sensors_rejected():
    with pytest.raises(ValueError):
        SensorModel([], [], seed=1)