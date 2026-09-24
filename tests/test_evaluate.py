"""Tests for industrial anomaly-evaluation metrics (ml/evaluate.py)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ml import (
    at_far_target,
    best_by_f1,
    build_metrics,
    persist_flags,
    threshold_sweep,
)


# ---------------------------------------------------------------------------
# persist_flags (debouncing)
# ---------------------------------------------------------------------------


def test_persist_flags_k3():
    flags = np.array([1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 0])
    out = persist_flags(flags, k=3)
    exp = np.array([0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0])
    np.testing.assert_array_equal(out, exp)


def test_persist_flags_k1_is_identity():
    flags = np.array([0, 1, 0, 1, 1, 0])
    np.testing.assert_array_equal(persist_flags(flags, k=1), flags)


def test_persist_flags_empty():
    np.testing.assert_array_equal(persist_flags(np.array([], dtype=int), k=3),
                                  np.array([], dtype=bool))


# ---------------------------------------------------------------------------
# build_metrics
# ---------------------------------------------------------------------------


def _case(onset=50, flag_start=None, n=100):
    """Scores with an anomaly window [onset, n) and flags starting
    at ``flag_start`` (None = never flagged)."""
    y = np.zeros(n, dtype=int)
    y[onset:] = 1
    scores = np.full(n, 0.1)
    scores[onset:] = 0.9
    if flag_start is not None:
        scores[:flag_start] = 0.1
        scores[flag_start:] = 1.5  # -> all flagged from flag_start
    else:
        scores[:] = 0.1
    return scores, y


def test_metrics_delayed_detection():
    scores, y = _case(onset=50, flag_start=55)  # raw flags start 5 s late
    m = build_metrics("m", "A", scores, y, threshold=1.0, fs=1.0, duration_s=100.0)
    # debounce (k=3) shifts the first *sustained* alarm by 2 more samples
    assert m.detection_delay_s == 7.0
    assert m.precision == 1.0
    assert m.recall == pytest.approx(0.86)      # first 2 anomalous samples lost to debounce
    assert m.false_alarm_rate == 0.0            # no healthy sample flagged
    assert m.f1 == pytest.approx(2 * 0.86 / 1.86)


def test_metrics_never_detected():
    scores, y = _case(onset=50, flag_start=None)
    m = build_metrics("m", "A", scores, y, threshold=9.0, fs=1.0, duration_s=100.0)
    assert m.detection_delay_s is None
    assert m.recall == 0.0


def test_metrics_requires_anomalies():
    scores = np.full(50, 0.5)
    y = np.zeros(50, dtype=int)
    with pytest.raises(ValueError):
        build_metrics("m", "A", scores, y, threshold=0.4, fs=1.0)


def test_metrics_counts_pre_onset_flags_as_false_alarms():
    # flag everything from t=0 (before true onset) -> 100 % F.A.R.
    scores = np.full(100, 2.0)
    y = np.zeros(100, dtype=int)
    y[50:] = 1
    m = build_metrics("m", "A", scores, y, threshold=1.0, fs=1.0, duration_s=100.0)
    assert m.recall == 1.0
    # the first 2 samples can never be sustained alarms (debounce k=3):
    # rows 2..49 are false alarms, rows 0..1 are clean
    assert m.false_alarm_rate == pytest.approx(48 / 50)
    assert m.false_alarms_per_day == pytest.approx(48 * 86400.0 / 100.0)


# ---------------------------------------------------------------------------
# threshold_sweep / operating points
# ---------------------------------------------------------------------------


def test_threshold_sweep_layout_and_operating_points():
    rng = np.random.default_rng(3)
    n = 300
    y = np.zeros(n, dtype=int)
    y[120:] = 1
    scores = rng.normal(0, 1, n)
    scores[120:] += 1.8

    sweep = threshold_sweep("m", "POOLED", scores, y, fs=1.0,
                            duration_s=300.0, n_thresholds=50)
    assert len(sweep) == 50
    for col in ["threshold", "f1", "precision", "recall",
                "false_alarm_rate", "detection_delay_s"]:
        assert col in sweep.columns

    best = best_by_f1(sweep)
    assert best["f1"] == sweep["f1"].max()
    assert best["recall"] > 0.9  # strong separation

    op = at_far_target(sweep, far_target=0.05)
    assert op["false_alarm_rate"] <= 0.05


def test_at_far_target_falls_back_when_unreachable():
    rng = np.random.default_rng(4)
    y = np.zeros(100, dtype=int)
    y[30:] = 1
    scores = rng.normal(0, 0.05, 100)  # tiny dynamic range: threshold can't kill all FPs
    sweep = threshold_sweep("m", "P", scores, y, n_thresholds=20)
    op = at_far_target(sweep, far_target=-0.5)  # impossible -> fallback to best-F1
    assert op["f1"] == sweep["f1"].max()