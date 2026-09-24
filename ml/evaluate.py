"""Anomaly-detection evaluation with industrial metrics.

Beyond precision/recall/F1 we report the two things maintenance engineers
actually care about:

  - false alarm rate  (FAR): fraction of healthy samples flagged, also
    expressed per day;
  - detection delay  : time from true fault onset to the first *sustained*
    alarm (K consecutive flagged samples, to suppress single-sample noise).

A ``threshold_sweep`` over scores produces a 2-column trade-off curve
(delay vs false-alarm rate); the runner selects operating points either by
best F1 or by a target FAR (the honest way to compare methods: at matched
false-alarm budgets).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    precision_recall_fscore_support,
    roc_auc_score,
)


@dataclass
class DetectionMetrics:
    method: str
    asset_id: str
    threshold: float
    n_true_anomalies: int
    n_flagged: int
    precision: float
    recall: float
    f1: float
    false_alarm_rate: float          # FP / (FP + TN) on healthy samples
    false_alarms_per_day: float
    detection_delay_s: float | None  # None = never detected
    auc: float
    pr_auc: float
    window_duration_s: float


def persist_flags(flags: np.ndarray, k: int) -> np.ndarray:
    """Alarm only when >= k of the last k samples are flagged (debouncing).

    Turns the raw per-sample flags into *sustained* alarms, which is the
    correct object for industrial systems (single-sample spikes are noise).
    """
    flags = flags.astype(bool)
    if k <= 1:
        return flags
    if len(flags) == 0:
        return flags
    conv = np.convolve(flags.astype(int), np.ones(k, dtype=int), mode="full")[:len(flags)]
    return conv >= k


def _delay_s(flags: np.ndarray, y_true: np.ndarray, onset_idx: int, fs: float) -> float | None:
    sustained = persist_flags(flags, k=3)
    hits = np.where(sustained & y_true)[0]
    # first sustained alarm at or after true onset
    cand = hits[hits >= onset_idx]
    if len(cand) == 0:
        return None
    return float(cand[0] - onset_idx) / fs


def build_metrics(
    method: str,
    asset_id: str,
    scores: np.ndarray,
    y_true: np.ndarray,
    threshold: float,
    fs: float = 1.0,
    duration_s: Optional[float] = None,
) -> DetectionMetrics:
    """Compute DetectionMetrics at one threshold.

    ``y_true`` is the per-sample anomaly ground truth (0/1). TRUE onset = the
    first anomalous sample. ``fs`` converts sample counts to seconds.
    """
    scores = np.asarray(scores, dtype=float)
    y_true = np.asarray(y_true, dtype=int)
    flags = scores >= threshold
    sustained = persist_flags(flags, k=3)

    if y_true.sum() == 0:
        raise ValueError("y_true has no anomalies; cannot compute detection metrics")

    onset = int(np.argmax(y_true))
    # only count alarms at/after onset as true positives (before onset = false alarm)
    tp = int(((sustained) & (y_true == 1)).sum())
    fp = int((sustained & (y_true == 0)).sum())
    fn = int(((y_true == 1) & (~sustained)).sum())
    tn = int(((y_true == 0) & (~sustained)).sum())

    prec = tp / (tp + fp) if (tp + fp) else float("nan")
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    far = fp / (fp + tn) if (fp + tn) else 0.0
    dur = duration_s if duration_s is not None else float(len(scores)) / fs
    far_day = fp * (86400.0 / dur) if dur > 0 else float("inf")

    valid = np.isfinite(scores)
    auc = float(roc_auc_score(y_true[valid], scores[valid])) if (y_true[valid].sum() > 0 and (y_true[valid] == 0).any()) else float("nan")
    prauc = float(average_precision_score(y_true[valid], scores[valid])) if y_true[valid].sum() > 0 else float("nan")

    return DetectionMetrics(
        method=method,
        asset_id=asset_id,
        threshold=float(threshold),
        n_true_anomalies=int(y_true.sum()),
        n_flagged=int(sustained.sum()),
        precision=prec,
        recall=rec,
        f1=f1,
        false_alarm_rate=far,
        false_alarms_per_day=far_day,
        detection_delay_s=_delay_s(scores >= threshold, y_true, onset, fs),
        auc=auc,
        pr_auc=prauc,
        window_duration_s=dur,
    )


def threshold_sweep(
    method: str,
    asset_id: str,
    scores: np.ndarray,
    y_true: np.ndarray,
    fs: float = 1.0,
    duration_s: Optional[float] = None,
    n_thresholds: int = 200,
) -> pd.DataFrame:
    """Return one row per threshold: metrics along the operating curve."""
    s = np.asarray(scores, dtype=float)
    if np.all(np.isnan(s)):
        raise ValueError("scores are all NaN")
    lo, hi = float(np.nanmin(s)), float(np.nanmax(s))
    hi = hi + 1e-9
    ths = np.linspace(lo, hi, n_thresholds)
    rows = []
    for th in ths:
        m = build_metrics(method, asset_id, s, np.asarray(y_true), th,
                          fs=fs, duration_s=duration_s)
        rows.append(m.__dict__)
    return pd.DataFrame(rows)


def best_by_f1(sweep: pd.DataFrame) -> pd.Series:
    return sweep.loc[sweep["f1"].fillna(-1).idxmax()]


def at_far_target(sweep: pd.DataFrame, far_target: float = 0.01) -> pd.Series:
    """Operating point with the highest recall among thresholds whose
    false-alarm rate does not exceed ``far_target``."""
    ok = sweep[sweep["false_alarm_rate"] <= far_target]
    if ok.empty:
        return best_by_f1(sweep)
    return ok.loc[ok["recall"].fillna(-1).idxmax()]