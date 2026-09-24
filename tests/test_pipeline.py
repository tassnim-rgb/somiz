"""Tests for the preprocessing pipeline: validation, imputation,
normalisation (fit-on-train-only), rolling features, chronological splits,
and anti-leakage guarantees."""

import numpy as np
import pandas as pd
import pytest

from pipeline.preprocess import PreprocessConfig, Preprocessor
from pipeline.split import chrono_split, expanding_window_cv
from pipeline.features import rolling_features, rate_of_change, spectral_features_frame
from simulation import SimulationConfig, FaultSpec, Simulator


def _run(duration=300.0, fault=None, seed=3, clean=False):
    op = __import__("simulation.config", fromlist=["OperatingProfileSpec"]).OperatingProfileSpec
    segs = [(60, 0.6)] if duration <= 60 else [(60, 0.6), (duration, 0.9)]
    kwargs = {"faults": [fault] if fault else []}
    if clean:
        from simulation.config import default_sensor_set
        from dataclasses import replace
        kwargs["sensors"] = [replace(s, missing_p=0.0, outlier_p=0.0) for s in default_sensor_set()]
    cfg = SimulationConfig(seed=seed, duration_s=duration, fs_hz=1.0, dt_phys=0.1,
                           profile=op(segments=segs, cycle=False), **kwargs)
    return Simulator(cfg).run().df


# ---------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------


def test_validation_ok_on_clean_frame():
    pp = Preprocessor()
    rep = pp.validate(_run())
    assert rep.ok
    assert rep.n_rows > 0


def test_validation_flags_missing_column():
    df = _run().drop(columns=["flow"])
    pp = Preprocessor()
    rep = pp.validate(df)
    assert not rep.ok
    assert any("flow" in i for i in rep.issues)


def test_validation_flags_unsorted_time():
    df = _run().sample(frac=1, random_state=1).reset_index(drop=True)
    pp = Preprocessor()
    assert not pp.validate(df).ok


def test_validation_flags_out_of_range_sensor():
    df = _run()
    df.loc[5, "vib"] = 999.0
    pp = Preprocessor()
    rep = pp.validate(df)
    assert not rep.ok
    assert any("vib" in i for i in rep.issues)


def test_validation_reports_nan_census():
    df = _run(clean=True).copy()
    df.loc[10:12, "flow"] = np.nan
    rep = Preprocessor().validate(df)
    assert rep.n_nan_by_column.get("flow") == 3


# ---------------------------------------------------------------------
# Imputation
# ---------------------------------------------------------------------


def test_linear_imputation_fills_gap():
    df = _run(duration=60.0).copy()
    df.loc[20:25, "vib"] = np.nan
    pp = Preprocessor(PreprocessConfig(impute="linear", normalize="none",
                                       add_anomaly_target=False,
                                       add_rate_of_change=False, rolling_window=0))
    out = pp.fit_transform(df)
    assert not out["vib"].isna().any()


def test_imputation_none_keeps_nan():
    df = _run(duration=60.0).copy()
    df.loc[20, "vib"] = np.nan
    pp = Preprocessor(PreprocessConfig(impute="none", normalize="none",
                                       add_anomaly_target=False,
                                       add_rate_of_change=False, rolling_window=0))
    out = pp.fit_transform(df)
    assert out["vib"].isna().any()


# ---------------------------------------------------------------------
# Normalisation fits on the fit slice only (anti-leakage)
# ---------------------------------------------------------------------


def test_scaler_fit_on_train_only_normalises_test_without_refit():
    df = _run(duration=300.0)
    pp = PreprocessConfig(impute="linear", normalize="zscore",
                          add_anomaly_target=False, add_rate_of_change=False,
                          rolling_window=0)
    fit, val, test = Preprocessor(pp).split_transform(df, fit_frac=0.5, val_frac=0.25)
    # fit-slice should be ~N(0,1)
    assert fit["vib"].mean() == pytest.approx(0.0, abs=1e-9)
    assert fit["vib"].std() == pytest.approx(1.0, abs=1e-9)
    # test-slice uses the SAME scaler -> mean not necessarily 0 but finite
    assert np.isfinite(test["vib"]).all()


def test_leakage_guard_order_preserved():
    """Rolling features at row t must NOT depend on future rows."""
    df = _run(duration=400.0)
    out = rolling_features(df, ["vib"], window=60, shift=1)
    col = out["vib_roll60_mean"].to_numpy()
    raw = df["vib"].to_numpy()
    for i in [50, 100, 200]:
        window = raw[max(0, i - 60):i]  # strictly past values (shift=1 => exclude i)
        assert col[i] == pytest.approx(window.mean(), abs=1e-9)


def test_constant_column_dropped_from_standardisation():
    df = _run(duration=120.0)
    df["power"] = 42.0  # force a constant column
    pp = PreprocessConfig(impute="linear", normalize="zscore",
                          add_anomaly_target=False, add_rate_of_change=False,
                          rolling_window=0)
    pre = Preprocessor(pp)
    out = pre.fit_transform(df)
    assert out["power"].nunique() <= 1  # not standardised (variance zero)


# ---------------------------------------------------------------------
# Splits
# ---------------------------------------------------------------------


def test_chrono_split_contiguous_and_ordered():
    df = _run(duration=300.0)
    fit, val, test = chrono_split(df, 0.5, 0.25)
    assert len(fit) + len(val) + len(test) == len(df)
    assert fit["t"].max() <= val["t"].min()
    assert val["t"].max() <= test["t"].min()
    # identical ordering to the source (never shuffled)
    assert (fit["t"].to_numpy() == df["t"].to_numpy()[:len(fit)]).all()


def test_chrono_split_bad_fractions():
    df = _run()
    with pytest.raises(ValueError):
        chrono_split(df, 0.0, 0.2)
    with pytest.raises(ValueError):
        chrono_split(df, 0.6, 0.6)


def test_chrono_split_rejects_unordered():
    df = _run().sample(frac=1, random_state=0).reset_index(drop=True)
    with pytest.raises(ValueError):
        chrono_split(df, 0.5, 0.2)


def test_expanding_window_cv_grows_and_no_leak():
    df = _run(duration=900.0)
    folds = list(expanding_window_cv(df, n_folds=3, min_fit=200, horizon=10))
    assert len(folds) >= 2
    sizes = [len(tr) for tr, _ in folds]
    assert sizes == sorted(sizes)  # expanding
    for tr, va in folds:
        # purge gap: validation starts after train end + horizon
        assert va["t"].min() >= tr["t"].max() + 10 - 1e-9


# ---------------------------------------------------------------------
# Features
# ---------------------------------------------------------------------


def test_rolling_features_columns():
    out = rolling_features(_run(), ["vib", "flow"], window=30)
    for c in ["vib_roll30_mean", "vib_roll30_std", "flow_roll30_max", "flow_roll30_median"]:
        assert c in out.columns


def test_rate_of_change_columns():
    out = rate_of_change(_run(), ["vib"])
    assert "vib_delta" in out.columns and "vib_delta_abs" in out.columns


def test_spectral_features_shape_and_units():
    df = _run(duration=300.0)
    spec = spectral_features_frame(df, ["vib"], fs_hz=1.0, window=64, stride=32)
    assert len(spec) >= 3
    assert "vib_spec_dom_hz" in spec.columns
    assert spec["vib_spec_dom_hz"].between(0, 0.5).all()  # <= Nyquist at 1 Hz
    assert spec["vib_spec_low_ratio"].between(0, 1).all()
    assert spec["t_start"].is_monotonic_increasing


def test_spectral_features_handles_nan_windows():
    df = _run(duration=120.0)
    df.loc[30:40, "vib"] = np.nan
    spec = spectral_features_frame(df, ["vib"], fs_hz=1.0, window=32, stride=16)
    assert np.isfinite(spec["vib_spec_dom_hz"]).all()


# ---------------------------------------------------------------------
# End-to-end split_transform with targets
# ---------------------------------------------------------------------


def test_split_transform_adds_binary_target():
    df = _run(duration=600.0, fault=FaultSpec("bearing", onset_s=200, target=1.0, duration_s=300))
    fit, val, test = Preprocessor().split_transform(df, 0.5, 0.25)
    for part in (fit, val, test):
        assert "anomaly_target" in part.columns
        assert set(part["anomaly_target"].unique()) <= {0, 1}
    # later (val/test) must contain anomalies given the fault
    assert test["anomaly_target"].sum() > 0


def test_preprocessor_log_documents_steps():
    pp = Preprocessor()
    pp.split_transform(_run(duration=300.0), 0.5, 0.25)
    log = pp.report()
    assert "impute" in log and "scaler" in log and "rolling" in log