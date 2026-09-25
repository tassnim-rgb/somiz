#!/usr/bin/env python
"""Phase 9 research experiments (twin-vs-ML detection, noise robustness,
early detection, FA/FN tradeoff, optimisation value sensitivity).

Everything here consumes SIMULATED physics runs. The health "twin" detector
is the Phase 4 time-indexed health index (commissioning reference curve);
the "statistical ML" detector is the RMS z-score baseline; "hybrid" scores
the standardised mean of both. No detector is trained on ground truth.

Runtime is bounded: 17 short runs (900 s), statistical scorers only, and a
handful of MILP solves. Adds/reuses NO heavy model training.

Writes experiments/results/research_comparison.json (tracked artefact).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from dataengine.generator import DatasetGenerator, AssetRunSpec
from digital_twin import HealthIndex, HealthIndexConfig
from ml.anomaly import StatisticalBaselineDetector
from optimization import (
    AssetPlanningInput,
    SchedulerInput,
    do_nothing_policy,
    greedy_schedule,
    milp_schedule,
)
from simulation import Simulator, SimulationConfig
from simulation.config import FaultSpec

SENSOR_COLS = ["vib", "t_motor", "t_fluid", "p_disch", "flow",
               "rpm", "current", "power", "efficiency"]
WARMUP_S = 120.0
DURATION_S = 900.0
TARGETS = {"bearing": 1.0, "overheating": 0.9, "leakage": 0.8,
           "impeller": 0.7, "blockage": 0.7}
ONSETS = [100.0, 300.0, 500.0]


def build_frame(scenario: str, onset: float, seed: int) -> pd.DataFrame:
    cfg = SimulationConfig(seed=seed, duration_s=DURATION_S, fs_hz=1,
                           stop_on_failure=False)
    if scenario != "healthy":
        # constant progression ramp so a later onset differs only in when the
        # fault starts, not in how fast severity grows (avoids a confound in
        # the early-detection experiment)
        cfg.faults = [FaultSpec(scenario, onset_s=onset, target=TARGETS[scenario],
                                duration_s=450.0)]
    return Simulator(cfg).run().df


def steady_mask(t: np.ndarray) -> np.ndarray:
    return t >= WARMUP_S


def stat_score(det, frame: pd.DataFrame) -> np.ndarray:
    s = det.score(frame)
    s = s.astype(float)
    s[~np.isfinite(s)] = 0.0
    return s


def twin_score(hi: HealthIndex, frame: pd.DataFrame) -> np.ndarray:
    ev = hi.evaluate(frame)
    hi_v = ev["hi"].to_numpy(dtype=float)
    d = -hi.cfg.tau * np.log(np.clip(hi_v / 100.0, 1e-6, 1.0))
    d[~np.isfinite(d)] = np.nan
    return d


def severity_at_first_detection(score: np.ndarray, t: np.ndarray,
                                sev: np.ndarray, theta: float,
                                onset: float) -> float | None:
    above = np.where((score >= theta) & (t >= onset))[0]
    if above.size == 0:
        return None
    return float(sev[above[0]])


def detection_delay(score: np.ndarray, t: np.ndarray, sev: np.ndarray,
                    theta: float, onset: float) -> float | None:
    above = score >= theta
    active = sev >= 0.05
    candidate = np.where(above & (t >= onset))[0]
    if candidate.size == 0:
        return None
    return float(t[candidate[0]] - onset)


def far(score: np.ndarray, theta: float) -> float:
    return float(np.mean(score >= theta))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--noise-levels", default="0.25,0.5,1.0,2.0,4.0")
    ap.add_argument("--cost-fractions", default="0.05,0.10,0.15,0.20,0.25")
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)

    # ---------------------------------------------------------- fleet
    t0 = time.time()
    frames: dict = {}
    for scen in ["healthy", *TARGETS]:
        for onset in ([0.0] if scen == "healthy" else ONSETS):
            key = (scen, onset)
            frames[key] = build_frame(scen, onset, args.seed + len(frames))
    healthy = frames[("healthy", 0.0)]

    # ------------------------------------------------- exp 1: detectors
    hi = HealthIndex(HealthIndexConfig(warmup_s=WARMUP_S)).fit(healthy)
    det = StatisticalBaselineDetector(sensors=SENSOR_COLS, smooth=15).fit(healthy)

    t = healthy["t"].to_numpy(dtype=float)
    s_hi = twin_score(hi, healthy)
    s_det = stat_score(det, healthy)
    m = steady_mask(t)
    # standardise for the hybrid score (against the healthy reference)
    def _std(arr: np.ndarray) -> float:
        v = float(np.nanstd(arr))
        return 1.0 if (not np.isfinite(v) or v == 0.0) else v

    mu_hi, sd_hi = float(np.nanmean(s_hi[m])), _std(s_hi[m])
    mu_det, sd_det = float(np.mean(s_det[m])), _std(s_det[m])

    detectors = {}
    per_mode = {}
    for scen in TARGETS:
        f = frames[(scen, 300.0)]
        tv = f["t"].to_numpy(dtype=float)
        sv = f["fault_severity"].to_numpy(dtype=float)
        msk = steady_mask(tv) & np.isfinite(sv)
        pos = sv[msk] >= 0.05
        sc_t = twin_score(hi, f)[msk]
        sc_d = stat_score(det, f)[msk]
        sc_h = (sc_t - mu_hi) / sd_hi * 0.5 + (sc_d - mu_det) / sd_det * 0.5
        row = {
            "scenario": scen,
            "auc_twin": float(roc_auc_score(pos, np.nan_to_num(sc_t))),
            "auc_statistical": float(roc_auc_score(pos, sc_d)),
            "auc_hybrid": float(roc_auc_score(pos, sc_h)),
        }
        # delay at threshold with ~2% FAR on the healthy reference
        th_t = float(np.nanquantile(s_hi[m], 0.98))
        th_d = float(np.quantile(s_det[m], 0.98))
        row["delay_twin_s"] = detection_delay(
            np.nan_to_num(twin_score(hi, f)), tv, sv, th_t, 300.0)
        row["delay_statistical_s"] = detection_delay(
            stat_score(det, f), tv, sv, th_d, 300.0)
        row["far_twin_pct"] = round(far(s_hi[m], th_t) * 100.0, 2)
        row["far_statistical_pct"] = round(far(s_det[m], th_d) * 100.0, 2)
        per_mode[scen] = row
        detectors[f"{scen}@300s"] = row

    # ------------------------------------------------- exp 2: noise
    noise_levels = [float(x) for x in args.noise_levels.split(",")]
    noise_rows = []
    base = frames[("bearing", 300.0)]
    ref_stats = {c: float(np.std(healthy[c].to_numpy(dtype=float)))
                 for c in SENSOR_COLS}
    for mult in noise_levels:
        noisy = base.copy()
        for c in SENSOR_COLS:
            clean = base[c].to_numpy(dtype=float)
            noisy[c] = clean + rng.normal(0.0, ref_stats[c] * mult, len(clean))
        h_noisy = healthy.copy()
        for c in SENSOR_COLS:
            clean = healthy[c].to_numpy(dtype=float)
            h_noisy[c] = clean + rng.normal(0.0, ref_stats[c] * mult, len(clean))
        d_n = StatisticalBaselineDetector(sensors=SENSOR_COLS, smooth=15).fit(h_noisy)
        sc_ref = stat_score(d_n, h_noisy)
        tv = noisy["t"].to_numpy(dtype=float)
        sv = noisy["fault_severity"].to_numpy(dtype=float)
        msk = steady_mask(tv)
        theta = float(np.quantile(sc_ref[msk], 0.98))
        delay = detection_delay(stat_score(d_n, noisy), tv, sv, theta, 300.0)
        sev_at = severity_at_first_detection(
            stat_score(d_n, noisy), tv, sv, theta, 300.0)
        noise_rows.append({
            "noise_multiplier": mult,
            "far_pct": round(far(sc_ref[msk], theta) * 100.0, 2),
            "delay_s": delay,
            "severity_at_detection": sev_at,
        })

    # ------------------------------------------------- exp 3: early det
    early_rows = []
    for scen in TARGETS:
        for onset in ONSETS:
            f = frames[(scen, onset)]
            tv = f["t"].to_numpy(dtype=float)
            sv = f["fault_severity"].to_numpy(dtype=float)
            msk = steady_mask(tv)
            theta = float(np.quantile(s_det[m], 0.98))
            delay = detection_delay(stat_score(det, f), tv, sv, theta, onset)
            early_rows.append({
                "scenario": scen, "onset_s": onset, "delay_s": delay,
            })

    # ------------------------------------------------- exp 4: FA/FN curve
    threshs = np.linspace(0.5, 6.0, 56)
    curve = []
    for th in threshs:
        far_v = far(s_det[m], float(th))
        miss = []
        nmiss = ntot = 0
        for scen in TARGETS:
            f = frames[(scen, 300.0)]
            tv = f["t"].to_numpy(dtype=float)
            sv = f["fault_severity"].to_numpy(dtype=float)
            msk = steady_mask(tv)
            sc = stat_score(det, f)[msk]
            act = sv[msk] >= 0.05
            det_v = sc >= float(th)
            miss.append(float(np.mean(~det_v[act])))  # miss among fault samples
            nmiss += int(np.sum(act & ~det_v))
            ntot += int(np.sum(act))
        curve.append({
            "threshold": round(float(th), 2),
            "far_pct": round(far_v * 100.0, 2),
            "miss_pct": round(float(np.mean(miss)) * 100.0, 2),
            "miss_samples": int(nmiss),
            "fault_samples": int(ntot),
        })
    # best-F1 operating point
    best = min(curve, key=lambda r: abs(r["far_pct"] - r["miss_pct"]))

    # ------------------------------------------------- exp 5: opt value
    cost_rows = []
    for frac in [float(x) for x in args.cost_fractions.split(",")]:
        fleet = [
            AssetPlanningInput(asset_id=f"A{i}",
                               rul_days={"p10": 2.0, "p50": 4.0, "p90": 7.0},
                               failure_cost=250_000.0,
                               maintenance_cost=250_000.0 * frac) for i in range(6)
        ]
        for cap in (2, 1):
            inp = SchedulerInput(assets=fleet, horizon_days=14,
                                 capacity_per_day=cap,
                                 no_maintenance_days=[6, 13])
            m = milp_schedule(inp)
            g = greedy_schedule(inp)
            dn = do_nothing_policy(inp)
            cost_rows.append({
                "cost_fraction": frac,
                "capacity_per_day": cap,
                "milp": round(float(m["objective"]), 0),
                "greedy": round(float(g["objective"]), 0),
                "do_nothing": round(float(dn["objective"]), 0),
                "milp_vs_greedy_pct": round(
                    (m["objective"] / g["objective"] - 1.0) * 100.0, 1),
                "milp_vs_nothing_pct": round(
                    (m["objective"] / dn["objective"] - 1.0) * 100.0, 1),
            })

    # ------------------------------------------------- summary + export
    result = {
        "simulated": True,
        "fleet": {"duration_s": DURATION_S, "scenarios": list(TARGETS),
                  "onsets_s": ONSETS, "warmup_s": WARMUP_S},
        "exp1_detector_comparison": {"twin": "health-index D (time-indexed reference)",
                                     "statistical": "RMS z-score baseline",
                                     "hybrid": "standardised mean of both",
                                     "per_mode": per_mode},
        "exp2_noise_robustness": {"detector": "statistical", "rows": noise_rows},
        "exp3_early_detection": {"rows": early_rows},
        "exp4_fa_fn_tradeoff": {"thresholds": curve,
                                 "operating_point": best,
                                 "criteria": "min |FAR - miss|"},
        "exp5_optimisation_value": {"rows": cost_rows,
                                    "note": "savings are negative percentages "
                                            "of the baseline cost"},
        "runtime_s": round(time.time() - t0, 1),
    }
    out = ROOT / "experiments" / "results" / "research_comparison.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"[research] ran in {result['runtime_s']} s; wrote {out}")
    print("\nExp 1: detector comparison at 2% FAR (onset 300 s)")
    hdr = ("scenario", "auc_twin", "auc_stat", "auc_hybrid", "d_twin", "d_stat")
    print(" | ".join(hdr))
    for scen, r in per_mode.items():
        print(f"{scen:10s} | {r['auc_twin']:.3f} | {r['auc_statistical']:.3f} "
              f"| {r['auc_hybrid']:.3f} | {r['delay_twin_s']} | {r['delay_statistical_s']}")
    print("\nExp 2: noise robustness (statistical detector)")
    for r in noise_rows:
        print(f"  noise x{r['noise_multiplier']:>4}: FAR {r['far_pct']}%  delay {r['delay_s']} s")
    print("\nExp 3: early detection (delay by onset)")
    for r in early_rows:
        print(f"  {r['scenario']:10s} onset {r['onset_s']:>3}: delay {r['delay_s']} s")
    print("\nExp 4: FA/FN operating point")
    print(f"  {best}")
    print("\nExp 5: optimisation value by cost structure")
    for r in cost_rows:
        print(f"  frac {r['cost_fraction']:>5} cap {r['capacity_per_day']}: "
              f"MILP {r['milp']:.0f}  greedy {r['greedy']:.0f}  none "
              f"{r['do_nothing']:.0f}  (vs greedy {r['milp_vs_greedy_pct']}%, "
              f"vs nothing {r['milp_vs_nothing_pct']}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())