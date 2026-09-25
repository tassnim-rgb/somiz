"""Fault diagnosis: which failure mode is acting on the asset.

Two families:

  1. ``HeuristicFaultClassifier`` — a rule-based, *no-ML* reference built from
     the documented physics signatures (vibration for bearing wear, motor
     temperature for cooling faults, flow/pressure for hydraulic faults).
     It is the honest 'before machine learning' bar, not a strawman: it uses
     only steady-state healthy statistics and simple thresholds.
  2. Supervised classifiers trained in scripts/run_diagnosis_experiment.py
     (Random Forest, gradient boosting, MLP) on the same feature frames.

Ground truth labels come from the simulator: ``fault_labels()`` maps each
sample to its dominant active fault, or 'healthy' below an early-severity
threshold. In a real deployment the same labels come from engineering
inspection records; nothing here claims real-plant data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)

FaultId = str  # e.g. "bearing", "overheating", "leakage", "impeller", "blockage"
HEALTHY = "healthy"


# ---------------------------------------------------------------------------
# labels
# ---------------------------------------------------------------------------


def fault_labels(frame: pd.DataFrame,
                 severity_threshold: float = 0.05) -> pd.Series:
    """Per-sample class label from simulator ground truth.

    Samples with ``fault_severity < severity_threshold`` are 'healthy'
    (no active fault); otherwise the dominant active fault is used.
    """
    sev = frame["fault_severity"].to_numpy(dtype=float)
    dom = frame["dominant_fault"].to_numpy()
    lab = np.where(sev >= severity_threshold, dom, HEALTHY)
    return pd.Series(lab, index=frame.index)


# ---------------------------------------------------------------------------
# rule-based reference
# ---------------------------------------------------------------------------

# Rules evaluated in order; first match wins. z = trailing smoothed z-score
# of the sensor against the healthy reference (steady state only).
#
# Ordering note (physics-justified, see docs/DIAGNOSIS_RUL.md): in the SIM
# the overheating fault raises motor temperature *slowly* (thermal inertia)
# but also perturbs vibration a lot. A simple vibration rule alone cannot
# separate bearing wear from an overheating fault, so the thermal channel is
# checked first with a lower threshold: it is the specific discriminator.
HEURISTIC_RULES: List[Tuple[FaultId, str]] = [
    ("overheating", "t_motor >= 2.5"),
    ("bearing", "vib >= 3.0"),
    ("blockage", "p_disch >= 3.0 and flow <= -2.0"),
    ("impeller", "efficiency <= -3.0"),
    ("leakage", "flow <= -2.0 and p_disch <= -2.0"),
]


@dataclass
class HeuristicFaultClassifier:
    """Threshold-based reference classifier on physics signatures.

    ``fit`` stores per-sensor mean/std over the steady-state part of a
    healthy qualification run; ``predict`` smooths the z-scores with a
    trailing window and applies the documented rules.
    """

    sensors: List[str]
    warmup_s: float = 120.0
    smooth: int = 30
    z_threshold: float = 3.0
    heat_z_threshold: float = 2.5  # thermal channel fires earlier than vib

    def __post_init__(self):
        self._stats: Dict[str, Tuple[float, float]] = {}

    def fit(self, healthy_df: pd.DataFrame) -> "HeuristicFaultClassifier":
        cols = [c for c in self.sensors if c in healthy_df.columns]
        if not cols:
            raise ValueError("no usable sensor columns")
        self.sensors = cols
        df = healthy_df
        if "t" in df.columns and self.warmup_s > 0:
            df = df[df["t"] >= self.warmup_s]
        for c in cols:
            v = df[c].to_numpy(dtype=float)
            v = v[np.isfinite(v)]
            sd = float(np.std(v))
            if sd < 1e-12:
                sd = 1.0
            self._stats[c] = (float(np.mean(v)), sd)
        return self

    def _z_smoothed(self, frame: pd.DataFrame) -> pd.DataFrame:
        z = {}
        for c in self.sensors:
            mu, sd = self._stats[c]
            col = (frame[c].to_numpy(dtype=float) - mu) / sd
            col = col if self.smooth <= 1 else \
                pd.Series(col).rolling(self.smooth, min_periods=1).mean().to_numpy()
            z[c] = col
        return pd.DataFrame(z, index=frame.index)

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        """Class label per sample, from physics-signature rules.

        Rules apply in list order and only to samples not yet labelled
        (first match wins); later rules cannot overwrite a specific
        signature that fired earlier.
        """
        if not self._stats:
            raise RuntimeError("predict() before fit()")
        z = self._z_smoothed(frame)
        out = np.full(len(frame), HEALTHY, dtype=object)
        free = np.ones(len(frame), dtype=bool)
        # order matters: strongest / most specific signature first
        for fault, _expr in HEURISTIC_RULES:
            if fault not in z.columns and fault not in ("bearing", "overheating"):
                continue
            cond = self._eval_rule(z, fault, _expr)
            assign = cond & free
            out[assign] = fault
            free[assign] = False
        return out.astype(str)

    def _eval_rule(self, z: pd.DataFrame, fault: FaultId, expr: str) -> np.ndarray:
        get = lambda c: z[c].to_numpy(dtype=float) if c in z.columns \
            else np.zeros(len(z))
        vib = get("vib")
        t_motor = get("t_motor")
        p_disch = get("p_disch")
        flow = get("flow")
        efficiency = get("efficiency")
        if fault == "bearing":
            return vib >= self.z_threshold
        if fault == "overheating":
            return t_motor >= self.heat_z_threshold
        if fault == "blockage":
            return (p_disch >= self.z_threshold) & (flow <= -2.0)
        if fault == "impeller":
            return efficiency <= -self.z_threshold
        if fault == "leakage":
            return (flow <= -2.0) & (p_disch <= -2.0)
        raise ValueError(f"unknown rule target {fault!r}")


# ---------------------------------------------------------------------------
# severity estimation + calibration
# ---------------------------------------------------------------------------


def multiclass_brier(y_true: np.ndarray, proba: np.ndarray,
                     class_names: List[str]) -> float:
    """Multi-class Brier score (lower = better calibrated).

    proba[row k, class c] is the model's probability for class c.
    Brier = mean over samples of sum_c (one-hot(c) - proba[c])^2.
    """
    onehot = np.zeros_like(proba, dtype=float)
    for i, lab in enumerate(y_true):
        if lab in class_names:
            onehot[i, class_names.index(lab)] = 1.0
    return round(float(np.mean(np.sum((onehot - proba) ** 2, axis=1))), 5)


class SeverityRegressor:
    """Predicts the (0..1) fault severity from features.

    Twin of the RUL regression but for the *current* damage level; used by
    the decision-support layer for "how bad is this fault right now?",
    e.g. the ``severity_estimate`` field of the diagnoses table.
    Trained on fault-active samples only; targets are SIMULATED
    ``fault_severity`` values. A Ridge is the linear baseline, a
    GradientBoosting regressor the main model.
    """

    def __init__(self, kind: str = "gbm", n_estimators: int = 250,
                 max_depth: int = 4, random_state: int = 42):
        self.kind = kind
        if kind == "ridge":
            from sklearn.linear_model import Ridge
            self.model = Ridge(alpha=1.0)
        elif kind == "gbm":
            from sklearn.ensemble import GradientBoostingRegressor
            self.model = GradientBoostingRegressor(
                n_estimators=n_estimators, max_depth=max_depth,
                learning_rate=0.05, random_state=random_state)
        else:
            raise ValueError(f"unknown kind {kind!r}")

    def fit(self, X: pd.DataFrame, severity: np.ndarray) -> "SeverityRegressor":
        self.model.fit(X, severity)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return np.clip(self.model.predict(X), 0.0, 1.0)


def evaluate_severity(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """MAE / RMSE in severity units (0..1)."""
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    return {
        "mae": round(float(mean_absolute_error(y_true, y_pred)), 4),
        "rmse": round(float(np.sqrt(mean_squared_error(y_true, y_pred))), 4),
        "n": int(len(y_true)),
        "bias": round(float(np.mean(y_pred - y_true)), 4),
    }


# ---------------------------------------------------------------------------
# evaluation
# ---------------------------------------------------------------------------


def evaluate_classification(y_true: np.ndarray, y_pred: np.ndarray,
                            class_names: Optional[List[str]] = None) -> dict:
    """Per-class precision/recall/F1 + macro/weighted summary + confusion."""
    names = class_names or sorted(set(y_true.tolist()))
    prec, rec, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=names, zero_division=0)
    per_class = {}
    for i, n in enumerate(names):
        per_class[n] = {
            "precision": round(float(prec[i]), 4),
            "recall": round(float(rec[i]), 4),
            "f1": round(float(f1[i]), 4),
            "support": int(support[i]),
        }
    macro_f1 = float(np.mean([per_class[n]["f1"] for n in names]))
    weighted = precision_recall_fscore_support(
        y_true, y_pred, average="weighted", zero_division=0)
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(float(weighted[2]), 4),
        "per_class": per_class,
        "confusion_counts": confusion_matrix(
            y_true, y_pred, labels=names).tolist(),
        "class_names": names,
    }