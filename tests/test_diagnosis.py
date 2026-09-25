"""Phase 5 tests: fault diagnosis (labels, rule-based reference, classifiers)."""

import numpy as np
import pandas as pd
import pytest

from sklearn.ensemble import RandomForestClassifier

from simulation import Simulator, SimulationConfig
from simulation.config import FaultSpec, OperatingProfileSpec
from ml.diagnosis import (
    HeuristicFaultClassifier,
    SeverityRegressor,
    evaluate_classification,
    evaluate_severity,
    fault_labels,
    multiclass_brier,
)

SENSORS = ["vib", "t_motor", "t_fluid", "p_disch", "flow",
           "rpm", "current", "power", "efficiency"]


def run_frame(seed: int, duration: float = 300, faults=None,
              stop_on_failure: bool = False) -> pd.DataFrame:
    cfg = SimulationConfig(seed=seed, duration_s=duration, fs_hz=1,
                           faults=faults or [], stop_on_failure=stop_on_failure)
    return Simulator(cfg).run().df


# ---------------------------------------------------------------------------
# labels
# ---------------------------------------------------------------------------


def test_fault_labels_split_by_severity():
    frame = run_frame(1, faults=[
        FaultSpec("bearing", onset_s=50, target=1.0, duration_s=160)])
    lab = fault_labels(frame)
    t = frame["t"].to_numpy()
    # pre-onset rows: no active fault -> healthy
    assert set(lab[t < 50].unique()) == {"healthy"}
    # well after onset, severity is clearly above the 0.05 early threshold
    assert set(lab[t >= 100].unique()) == {"bearing"}
    assert set(lab.unique()) == {"healthy", "bearing"}
    # near onset the severity ramp starts below the early threshold, so the
    # first degraded rows are still labelled healthy (documented behaviour)
    just_after = lab[(t >= 50) & (t < 60)]
    assert "healthy" in set(just_after.unique())
    assert (frame["fault_severity"] >= 0.05).any()
    # catalogue progression is linear from onset, target reached at onset+dur
    assert frame["fault_severity"].max() == pytest.approx(1.0, abs=1e-3)


def test_fault_labels_severity_threshold_boundary():
    # dominant_fault is set even when severity is still ~0; the label only
    # flips to the fault at the early-severity threshold
    frame = run_frame(2, faults=[
        FaultSpec("overheating", onset_s=60, target=0.9, duration_s=150)])
    assert (frame["dominant_fault"] == "overheating").any()
    lab = fault_labels(frame)
    sev = frame["fault_severity"].to_numpy()
    assert set(lab[sev < 0.05].unique()) == {"healthy"}


def test_fault_labels_healthy_frame():
    lab = fault_labels(run_frame(3))
    assert set(lab.unique()) == {"healthy"}


# ---------------------------------------------------------------------------
# rule-based reference
# ---------------------------------------------------------------------------


def test_heuristic_healthy_and_bearing():
    hc = HeuristicFaultClassifier(sensors=SENSORS)
    hc.fit(run_frame(4))
    # healthy frame: (almost) all healthy
    pred_healthy = hc.predict(run_frame(5))
    assert (pred_healthy == "healthy").mean() >= 0.98
    # bearing frame: majority bearing
    pred_bearing = hc.predict(run_frame(6, faults=[
        FaultSpec("bearing", onset_s=50, target=1.0, duration_s=160)]))
    assert (pred_bearing == "bearing").mean() >= 0.7


def test_heuristic_overheating_detected():
    # the experiment fits the rule reference on a flat 90 %-load healthy run
    # (same profile the fleet generator uses); match that here
    prof = OperatingProfileSpec(segments=[(3000.0, 0.9)], cycle=True)
    fit_cfg = SimulationConfig(seed=7, duration_s=3000, fs_hz=1, faults=[],
                               profile=prof, stop_on_failure=False)
    hc = HeuristicFaultClassifier(sensors=SENSORS)
    hc.fit(Simulator(fit_cfg).run().df)
    # thermal faults are slow: a 9000 s run so the motor-temperature channel
    # (the discrimination signal) has time to develop
    prof2 = OperatingProfileSpec(segments=[(9000.0, 0.9)], cycle=True)
    cfg = SimulationConfig(seed=8, duration_s=9000, fs_hz=1,
                           faults=[FaultSpec("overheating", onset_s=200,
                                             target=0.9, duration_s=6000)],
                           profile=prof2, stop_on_failure=False)
    frame = Simulator(cfg).run().df
    pred = hc.predict(frame)
    # the thermal rule fires once t_motor exceeds ~2.5 healthy-z (roughly the
    # second half of the run); vibration-only rules mistake this fault for
    # bearing wear, which is the documented weakness of the rule baseline
    assert (pred == "overheating").mean() >= 0.3


# ---------------------------------------------------------------------------
# supervised classifier (tiny, fast)
# ---------------------------------------------------------------------------

def _two_assets(scenario, target, seeds=(10, 11)):
    faults = [FaultSpec(scenario, onset_s=50, target=target, duration_s=160)]
    return [run_frame(s, faults=faults) for s in seeds]


def test_tiny_rf_diagnosis_beats_chance():
    (healthy_tr, healthy_te) = _two_assets("healthy", 0.0, seeds=(20, 21))
    (brg_tr, brg_te) = _two_assets("bearing", 1.0, seeds=(22, 23))
    (ovh_tr, ovh_te) = _two_assets("overheating", 0.9, seeds=(24, 25))

    def build(assets):
        Xs, ys = [], []
        for frame in assets:
            lab = fault_labels(frame)
            keep = lab != "healthy"
            Xs.append(frame.loc[keep, SENSORS])
            ys.append(lab[keep])
        return pd.concat(Xs), pd.concat(ys)

    X_tr, y_tr = build([healthy_tr, brg_tr, ovh_tr])
    X_te, y_te = build([brg_te, ovh_te])
    # healthy test rows: the healthy asset (all rows) + pre-onset rows
    X_te = pd.concat([X_te, healthy_te[SENSORS]])
    y_te = pd.concat([y_te, fault_labels(healthy_te)])

    rf = RandomForestClassifier(n_estimators=40, max_depth=4,
                                random_state=0).fit(X_tr, y_tr)
    rep = evaluate_classification(y_te.to_numpy(), rf.predict(X_te))
    assert rep["macro_f1"] >= 0.5
    assert set(rep["per_class"]) == {"healthy", "bearing", "overheating"}
    assert rep["per_class"]["bearing"]["f1"] >= 0.6


def test_evaluate_classification_schema():
    y = np.array(["a", "a", "b", "b", "c"])
    p = np.array(["a", "b", "b", "c", "c"])
    rep = evaluate_classification(y, p)
    # matches at positions 0, 2, 4 -> 3/5
    assert rep["accuracy"] == pytest.approx(0.6, abs=1e-9)
    assert "macro_f1" in rep and "weighted_f1" in rep
    assert set(rep["per_class"]) == {"a", "b", "c"}
    assert len(rep["confusion_counts"]) == 3


# ---------------------------------------------------------------------------
# calibration + severity estimation
# ---------------------------------------------------------------------------


def test_multiclass_brier_perfect_and_worst():
    y = np.array(["a", "b"])
    perfect = np.array([[1.0, 0.0], [0.0, 1.0]])
    assert multiclass_brier(y, perfect, ["a", "b"]) == 0.0
    wrong = np.array([[0.0, 1.0], [1.0, 0.0]])
    assert multiclass_brier(y, wrong, ["a", "b"]) == pytest.approx(2.0, abs=1e-9)


def test_severity_regressor_tracks_linear_ramp():
    rng = np.random.default_rng(11)
    X = rng.normal(size=(400, 4))
    sev = np.clip(0.15 * X[:, 0] + 0.5, 0.0, 1.0)
    Xdf = pd.DataFrame(X, columns=[f"f{i}" for i in range(4)])
    cut = 300
    ridge = SeverityRegressor("ridge").fit(Xdf.iloc[:cut], sev[:cut])
    gbm = SeverityRegressor("gbm", n_estimators=60).fit(Xdf.iloc[:cut], sev[:cut])
    for m in (ridge, gbm):
        rep = evaluate_severity(sev[cut:], m.predict(Xdf.iloc[cut:]))
        assert rep["mae"] < 0.25
        assert abs(rep["bias"]) <= 0.05
    # predictions are clipped to [0, 1]
    r = ridge.predict(Xdf)
    assert r.min() >= 0.0 and r.max() <= 1.0