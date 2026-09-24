#!/usr/bin/env python
"""Anomaly-detection experiment (Phase 4 deliverable).

Trains the four detectors and the health index on healthy data only
(unsupervised), then evaluates them on healthy + faulted assets with
industrial metrics: precision/recall/F1, AUC/PR-AUC, false-alarm rate
(per sample and per day) and detection delay. Results are written to
experiments/results/anomaly_comparison.json and printed as a table.

Usage:
  python scripts/run_anomaly_experiment.py [--seed 42] [--outdir ...]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from dataengine import AssetRunSpec, DatasetGenerator
from pipeline import Preprocessor
from digital_twin import HealthIndex
from ml import (
    IsolationForestDetector,
    PointAutoencoderDetector,
    StatisticalBaselineDetector,
    WindowedAutoencoderDetector,
    at_far_target,
    best_by_f1,
    build_metrics,
    threshold_sweep,
)

HEALTHY_ASSETS = ["HLT-01", "HLT-02", "HLT-03"]
FAULT_ASSETS = ["BRG-01", "OVH-01", "LEK-01"]
FAULT_SCENARIOS = ["bearing", "overheating", "leakage"]
DURATION = 21600.0
FIT_FRACTION = 0.6  # first 60 % of each healthy asset is training data

SENSOR_COLS = ["vib", "t_motor", "t_fluid", "p_disch", "flow",
               "rpm", "current", "power", "efficiency"]


def model_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only measurement + derived features (no ground-truth columns).

    Ground truth (health_stage, fault_severity, d_*, anomaly_target) must
    never reach a detector: that would be label leakage.
    """
    keep = [c for c in df.columns if c in SENSOR_COLS
            or c.endswith("_roll60_mean") or c.endswith("_roll60_std")
            or c.endswith("_delta") or c.endswith("_delta_abs")]
    return df[keep]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--outdir", default="data/generated/anomaly_experiment")
    args = ap.parse_args()

    t0 = time.time()
    outdir = Path(args.outdir)

    # -------- 1. deterministic dataset: 3 healthy + 3 faulted assets --------
    specs = [AssetRunSpec(a, "healthy", duration_s=DURATION) for a in HEALTHY_ASSETS]
    for aid, scen in zip(FAULT_ASSETS, FAULT_SCENARIOS):
        specs.append(AssetRunSpec(aid, scen, duration_s=DURATION))
    DatasetGenerator(master_seed=args.seed).generate(outdir, specs, formats=("parquet",))

    frames = {}
    for aid, scen in zip(HEALTHY_ASSETS + FAULT_ASSETS,
                         ["healthy"] * 3 + FAULT_SCENARIOS):
        frames[aid] = pd.read_parquet(outdir / f"{aid}__{scen}.parquet")

    # -------- 2. preprocessing (scaler fit on a healthy fit-slice) --------
    pp = Preprocessor()
    fit_asset = HEALTHY_ASSETS[0]
    pp.fit(frames[fit_asset].head(int(len(frames[fit_asset]) * FIT_FRACTION)))
    proc = {a: pp.transform(f) for a, f in frames.items()}
    healthy_eval = pd.concat([
        proc[a].tail(int(len(proc[a]) * (1 - FIT_FRACTION))) for a in HEALTHY_ASSETS
    ]).reset_index(drop=True)  # never seen by any detector

    healthy_fit = pd.concat([
        proc[a].head(int(len(proc[a]) * FIT_FRACTION)) for a in HEALTHY_ASSETS
    ]).reset_index(drop=True)
    train_sensors = healthy_fit[SENSOR_COLS]
    train_feat = model_frame(healthy_fit)

    # -------- 3. unsupervised detectors (healthy data only, no labels) --------
    detectors = {
        "statistical": StatisticalBaselineDetector(sensors=SENSOR_COLS),
        "isolation_forest": IsolationForestDetector(),
        "point_ae": PointAutoencoderDetector(sensors=SENSOR_COLS),
        "windowed_ae": WindowedAutoencoderDetector(window=32, sensors=SENSOR_COLS),
    }
    for m, det in detectors.items():
        X = train_feat if m == "isolation_forest" else train_sensors
        det.fit(X)

    # -------- 4. score every eval set (healthy tail + fault assets) --------
    scores = {}
    for m, det in detectors.items():
        scores[m] = {}
        scores[m]["HEALTHY_EVAL"] = det.score(
            model_frame(healthy_eval) if m == "isolation_forest" else healthy_eval[SENSOR_COLS])
        for aid in FAULT_ASSETS:
            scores[m][aid] = det.score(
                model_frame(proc[aid]) if m == "isolation_forest" else proc[aid][SENSOR_COLS])

    # -------- 5. health index (explainable, fit on same healthy data) --------
    # commissioning reference: time-indexed mean over the pooled healthy runs
    healthy_fit_raw = pd.concat([
        frames[a].head(int(len(frames[a]) * FIT_FRACTION)) for a in HEALTHY_ASSETS
    ]).reset_index(drop=True)
    hi = HealthIndex()
    hi.fit(healthy_fit_raw)
    hi_evals = {a: hi.validate(frames[a], asset_id=a)
                for a in HEALTHY_ASSETS + FAULT_ASSETS}

    # -------- 6. evaluation --------
    rows = []
    for m in detectors:
        pooled_s = np.concatenate([scores[m]["HEALTHY_EVAL"]]
                                  + [scores[m][a] for a in FAULT_ASSETS])
        pooled_y = np.concatenate([np.zeros(len(healthy_eval))]
                                  + [proc[a]["anomaly_target"].to_numpy()
                                     for a in FAULT_ASSETS])
        sweep = threshold_sweep(m, "POOLED", pooled_s, pooled_y, fs=1.0,
                                duration_s=DURATION, n_thresholds=150)
        best = best_by_f1(sweep)
        far2 = at_far_target(sweep, far_target=0.02)

        row = {
            "method": m,
            "auc": round(best["auc"], 4),
            "pr_auc": round(best["pr_auc"], 4),
            "f1_best": round(best["f1"], 4),
            "precision_best": _fmt(best["precision"]),
            "recall_best": round(best["recall"], 4),
            "far_best": round(best["false_alarm_rate"], 5),
            "far_day_best": round(best["false_alarms_per_day"], 2),
            "delay_s_best": _fmt(best["detection_delay_s"]),
            "far_at_2pct": round(far2["false_alarm_rate"], 5),
            "delay_s_at_far2": _fmt(far2["detection_delay_s"]),
            "threshold_best": round(best["threshold"], 4),
        }
        for aid in FAULT_ASSETS:
            mfr = build_metrics(m, aid, scores[m][aid],
                                proc[aid]["anomaly_target"].to_numpy(),
                                threshold=best["threshold"], fs=1.0,
                                duration_s=DURATION)
            row[f"delay_{aid}"] = _fmt(mfr.detection_delay_s)
        rows.append(row)

    hi_rows = []
    for aid in HEALTHY_ASSETS + FAULT_ASSETS:
        r = hi_evals[aid]
        hi_rows.append({
            "asset": aid,
            "hi_mean": round(r.hi_mean, 1),
            "hi_min": round(r.hi_min, 1),
            "pearson_r_with_severity": round(r.pearson_r_with_severity, 3),
            "stage_alignment": round(r.stage_alignment, 3),
        })

    results = {
        "experiment": "anomaly-detection",
        "phase": 4,
        "seed": args.seed,
        "n_healthy_train_samples": len(healthy_fit),
        "n_healthy_eval_samples": len(healthy_eval),
        "detectors": rows,
        "health_index": hi_rows,
        "elapsed_s": round(time.time() - t0, 1),
    }
    out_file = Path("experiments/results/anomaly_comparison.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(results, indent=2), encoding="utf-8")

    # -------- 7. report --------
    print(f"\n=== ANOMALY DETECTION COMPARISON (seed={args.seed}, {results['elapsed_s']}s) ===")
    print(f"{'method':16s} {'AUC':>6s} {'PR-AUC':>6s} {'F1':>6s} {'P':>6s} {'R':>6s} "
          f"{'FAR':>7s} {'FAR/day':>8s} {'delay':>7s} {'delay@FAR≤2%':>12s}")
    for r in rows:
        print(f"{r['method']:16s} {r['auc']:6.3f} {r['pr_auc']:6.3f} {r['f1_best']:6.3f} "
              f"{r['precision_best']:>6s} {r['recall_best']:6.3f} {r['far_best']:7.3f} "
              f"{r['far_day_best']:8.2f} {r['delay_s_best']:>7s} {r['delay_s_at_far2']:>12s}")
    print("\n--- per-fault-asset detection delay at pooled best-F1 threshold (s) ---")
    print(f"{'method':16s} " + " ".join(f"{a:>10s}" for a in FAULT_ASSETS))
    for r in rows:
        print(f"{r['method']:16s} " + " ".join(f"{r[f'delay_{a}']:>10s}" for a in FAULT_ASSETS))
    print("\n--- health index vs ground truth ---")
    print(f"{'asset':10s} {'HI mean':>8s} {'HI min':>7s} {'r(severity)':>12s} {'stage align':>11s}")
    for r in hi_rows:
        print(f"{r['asset']:10s} {r['hi_mean']:8.1f} {r['hi_min']:7.1f} "
              f"{r['pearson_r_with_severity']:12.3f} {r['stage_alignment']:11.3f}")
    print(f"\nresults json: {out_file}")
    return 0


def _fmt(v) -> str:
    if v is None:
        return "n/a"
    if isinstance(v, float):
        return f"{v:.1f}"
    return str(v)


if __name__ == "__main__":
    raise SystemExit(main())