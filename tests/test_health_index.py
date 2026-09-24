"""Tests for the explainable health index (digital_twin/health_index.py)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from simulation import FaultSpec, OperatingProfileSpec, SimulationConfig, Simulator
from digital_twin import HealthIndex, HealthIndexConfig


def _simulate(faults=None, duration=600.0, seed=7):
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


def _healthy_frame(duration=600.0, seed=7):
    return _simulate(faults=[], duration=duration, seed=seed)


def _bearing_frame(onset=120.0, duration=300.0):
    return _simulate(faults=[FaultSpec("bearing", onset_s=onset, target=1.0,
                                       duration_s=duration)], duration=500.0)


# ---------------------------------------------------------------------------
# config
# ---------------------------------------------------------------------------


def test_config_validation_rejects_bad_configs():
    with pytest.raises(ValueError):
        HealthIndex(HealthIndexConfig(tau=0.0))
    with pytest.raises(ValueError):
        HealthIndex(HealthIndexConfig(window=0))
    with pytest.raises(ValueError):
        HealthIndex(HealthIndexConfig(sensor_weights={}))
    with pytest.raises(ValueError):
        # genuinely gapped bands: (40,80] then [0,30] leaves (30,40) uncovered
        HealthIndex(HealthIndexConfig(bands=[("A", 40.0, 80.0), ("B", 0.0, 30.0)]))


def test_band_labels_follow_documented_scale():
    cfg = HealthIndexConfig()
    assert cfg.band_of(95.0) == "NORMAL"
    assert cfg.band_of(70.0) == "EARLY"
    assert cfg.band_of(50.0) == "MODERATE"
    assert cfg.band_of(30.0) == "SEVERE"
    assert cfg.band_of(5.0) == "FAILURE"


# ---------------------------------------------------------------------------
# behaviour
# ---------------------------------------------------------------------------


def test_healthy_machine_scores_high():
    hf = _healthy_frame()
    fit_slice = hf.head(int(len(hf) * 0.6))  # commissioning reference window
    hi = HealthIndex().fit(fit_slice)
    # evaluate over the same window: the machine matches its own reference
    ev = hi.evaluate(fit_slice)
    ev = ev[ev["hi_stage"] != "WARMUP"]      # steady state only
    assert ev["hi"].mean() > 80.0
    assert set(ev["hi_stage"].unique()) <= {"NORMAL", "EARLY"}


def test_evaluate_before_fit_raises():
    hi = HealthIndex()
    with pytest.raises(RuntimeError):
        hi.evaluate(_healthy_frame())


def test_fault_drives_index_down_and_tracks_severity():
    hf = _healthy_frame()
    bf = _bearing_frame()
    hi = HealthIndex().fit(hf.head(int(len(hf) * 0.6)))
    ev_health = hi.evaluate(hf.head(int(len(hf) * 0.6)))
    ev_fault = hi.evaluate(bf)
    ev_health = ev_health[ev_health["hi_stage"] != "WARMUP"]
    ev_fault = ev_fault[ev_fault["hi_stage"] != "WARMUP"]
    assert ev_health["hi"].mean() > ev_fault["hi"].mean()
    assert ev_fault["hi"].min() < 40.0

    rep = hi.validate(bf, asset_id="BRG-TEST")
    assert rep.pearson_r_with_severity < -0.5   # severity up -> HI down
    assert rep.hi_min == float(ev_fault["hi"].min())


def test_index_is_deterministic():
    hf = _healthy_frame()
    a = HealthIndex().fit(hf.head(200)).evaluate(hf)["hi"].to_numpy()
    b = HealthIndex().fit(hf.head(200)).evaluate(hf)["hi"].to_numpy()
    np.testing.assert_array_equal(a, b)


def test_constant_sensor_does_not_break_fit():
    hf = _healthy_frame()
    hf = hf.copy()
    hf["t_fluid"] = 25.0  # constant -> z forced to 0 by the baseline
    hi = HealthIndex().fit(hf.head(200))
    assert "t_fluid" in hi.member_sensors()
    ev = hi.evaluate(hf)
    assert np.isfinite(ev["hi"].dropna()).all()


def test_top_signals_provide_explainability():
    hf = _healthy_frame()
    bf = _bearing_frame()
    hi = HealthIndex().fit(hf.head(int(len(hf) * 0.6)))
    ev = hi.evaluate(bf)
    ev = ev[ev["hi_stage"] != "WARMUP"]
    assert "top_signals" in ev.columns
    names = {s for s in "+".join(ev["top_signals"]).split("+") if s}
    assert names <= set(hf.columns)
    # every entry lists exactly 3 weighted sensors
    assert all(len(row.split("+")) == 3 for row in ev["top_signals"])


def test_stage_alignment_and_confusion_are_reported():
    hf = _healthy_frame()
    bf = _bearing_frame()
    hi = HealthIndex().fit(hf.head(int(len(hf) * 0.6)))
    rep = hi.validate(bf, asset_id="BRG-TEST")
    assert 0.0 < rep.stage_alignment <= 1.0
    assert rep.band_confusion  # non-empty confusion dict
    assert rep.n_samples == len(bf)