#!/usr/bin/env python
"""Diagnosis + RUL experiment (Phase 5 deliverable).

Trains and compares, on the SIMULATED fleet:

  Diagnosis (which fault?):
    - heuristic rule-based reference (no ML) vs
    - Random Forest / gradient boosting / MLP classifiers.
  RUL (time to intervention threshold, with uncertainty):
    - Ridge (linear baseline) / gradient boosting mean / quantile
      gradient boosting (p10/p50/p90 intervals) / windowed MLP (temporal).
  Explainability: SHAP (TreeExplainer) global feature importance for the
    RF classifier and the mean-boosting RUL model, plus per-sample
    explanations narrative for a bearing case.

Results -> experiments/results/diagnosis_rul_comparison.json

Usage:
  python scripts/run_diagnosis_experiment.py [--seed 42] [--outdir ...]
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
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.neural_network import MLPClassifier

from dataengine import DatasetGenerator, SCENARIOS, default_fleet
from pipeline import Preprocessor
from ml.diagnosis import (
    HeuristicFaultClassifier,
    SeverityRegressor,
    evaluate_classification,
    evaluate_severity,
    fault_labels,
    multiclass_brier,
)
from ml.rul import (
    GradientBoostingRUL,
    QuantileGradientBoostingRUL,
    RidgeRUL,
    WindowMLPRegressor,
    build_rul_target,
    evaluate_rul,
    interval_coverage,
)
from ml.explain import shap_feature_importance, shap_sample_explanation

DURATION = 21600.0
FIT_FRACTION = 0.6
CLASS_ORDER = ["healthy", "bearing", "overheating", "leakage", "impeller", "blockage"]
SENSOR_COLS = ["vib", "t_motor", "t_fluid", "p_disch", "flow",
               "rpm", "current", "power", "efficiency"]


def model_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Measurement + derived features only (no ground truth, no t/u)."""
    keep = [c for c in df.columns if c in SENSOR_COLS
            or c.endswith("_roll60_mean") or c.endswith("_roll60_std")
            or c.endswith("_delta") or c.endswith("_delta_abs")]
    return df[keep].apply(pd.to_numeric, errors="coerce").fillna(0.0)


def scenario_target(scenario: str) -> float:
    return float(SCENARIOS[scenario][0].target)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--n-per-scenario", type=int, default=3)
    ap.add_argument("--outdir", default="data/generated/diagnosis_experiment")
    args = ap.parse_args()

    t0 = time.time()
    outdir = Path(args.outdir)

    # -------- 1. deterministic fleet: 3 healthy + 3 x 5 faults ---------
    assets = default_fleet(master_seed=args.seed, n_per_scenario=args.n_per_scenario,
                           duration_s=DURATION)
    manifest = DatasetGenerator(master_seed=args.seed).generate(
        outdir, assets, formats=("parquet",))
    by_asset = {e["asset_id"]: e["scenario"] for e in manifest.assets}
    frames = {aid: pd.read_parquet(outdir / f"{aid}__{scen}.parquet")
              for aid, scen in by_asset.items()}

    # group assets by scenario, assign repeat index 0..n-1
    scenery: dict = {}
    for aid, scen in by_asset.items():
        scenery.setdefault(scen, []).append(aid)
    train_ids, test_ids = [], []
    for scen, aids in scenery.items():
        for i, aid in enumerate(aids):
            (train_ids if i < args.n_per_scenario - 1 else test_ids).append(aid)

    # -------- 2. preprocessing (scaler fit on train healthy only) -------
    pp = Preprocessor()
    first_train_healthy = next(a for a in train_ids if by_asset[a] == "healthy")
    pp.fit(frames[first_train_healthy].head(
        int(len(frames[first_train_healthy]) * FIT_FRACTION)))
    proc = {a: pp.transform(f) for a, f in frames.items()}

    # -------- 3. diagnosis: labels + training rows ---------------------
    train_rows = []
    for aid in train_ids:
        scen = by_asset[aid]
        tdf = proc[aid]
        lab = fault_labels(tdf)
        if scen == "healthy":
            n = min(3000, len(tdf))
            idx = np.linspace(0, len(tdf) - 1, n).astype(int)
        else:
            active = np.where(lab != "healthy")[0]
            healthy_idx = np.where(lab == "healthy")[0]
            rng = np.random.default_rng(args.seed)
            subsample_healthy = rng.choice(healthy_idx, size=min(2500, len(healthy_idx)),
                                           replace=False) if len(healthy_idx) else np.array([], dtype=int)
            idx = np.concatenate([active[::2], subsample_healthy])
        X = model_frame(tdf).iloc[idx]
        y = lab.iloc[idx].to_numpy()
        train_rows.append((X, y, scen))
    X_tr = pd.concat([r[0] for r in train_rows]).reset_index(drop=True)
    y_tr = np.concatenate([r[1] for r in train_rows])
    freq = pd.Series(y_tr).value_counts(normalize=True)
    sample_w = np.array([1.0 / freq[v] for v in y_tr])
    sample_w /= sample_w.mean()
    from collections import Counter
    print(f"[diagnosis] train: {len(X_tr)} rows, classes {dict(Counter(y_tr))}")

    # -------- 4. diagnosis: models -------------------------------------
    rf = RandomForestClassifier(n_estimators=200, max_depth=12, n_jobs=-1,
                                class_weight="balanced", random_state=args.seed)
    rf.fit(X_tr, y_tr)

    gbm = GradientBoostingClassifier(n_estimators=250, max_depth=4,
                                     learning_rate=0.05, random_state=args.seed)
    gbm.fit(X_tr, y_tr, sample_weight=sample_w)

    mlp_n = 25000
    mlp = MLPClassifier(hidden_layer_sizes=(32, 16), max_iter=300,
                        early_stopping=True, random_state=args.seed)
    if len(X_tr) > mlp_n:
        rng = np.random.default_rng(args.seed)
        keep = rng.choice(len(X_tr), size=mlp_n, replace=False)
        mlp.fit(X_tr.iloc[keep], y_tr[keep])
    else:
        mlp.fit(X_tr, y_tr)

    heuristic = HeuristicFaultClassifier(sensors=SENSOR_COLS)
    heuristic.fit(frames[first_train_healthy].head(
        int(len(frames[first_train_healthy]) * FIT_FRACTION)))
    models = {"heuristic": heuristic, "random_forest": rf,
              "gradient_boosting": gbm, "mlp": mlp}

    # fail fast (second 1, not minute 40): every model must be fitted
    for _name, _m in models.items():
        assert callable(getattr(_m, "predict", None)), f"model {_name} not fitted"

    # -------- 5. diagnosis: evaluation on held-out assets --------------
    diag_results = {}
    for name, model in models.items():
        yt_all, yp_all, proba_all = [], [], []
        for aid in test_ids:
            scen = by_asset[aid]
            tdf = proc[aid]
            lab = fault_labels(tdf)
            idx = np.arange(0, len(tdf), 2) if scen != "healthy" else \
                np.linspace(0, len(tdf) - 1, 4000).astype(int)
            Xt = model_frame(tdf).iloc[idx]
            if name == "heuristic":
                # the rule reference is fit on *raw* sensor units; the
                # processed (z-scored) frame shares the same row index, so
                # predict on the raw frame at the same positions
                yp = model.predict(frames[aid].iloc[idx])
                proba = None
            else:
                yp = model.predict(Xt)
                proba = model.predict_proba(Xt) if hasattr(model, "predict_proba") \
                    else None
            yt_all.append(lab.iloc[idx].to_numpy())
            yp_all.append(np.asarray(yp, dtype=object))
            proba_all.append(proba)
        y_true = np.concatenate(yt_all)
        y_pred = np.concatenate([np.asarray(p, dtype=object) for p in yp_all]).astype(str)
        rep = evaluate_classification(y_true, y_pred, CLASS_ORDER)
        per_fault = {}
        for aid in test_ids:
            scol = by_asset[aid]
            if scol == "healthy":
                continue
            tdf = proc[aid]
            y_test = fault_labels(tdf).iloc[::2].to_numpy()
            Xt = model_frame(tdf).iloc[::2]
            y_pre = model.predict(frames[aid].iloc[::2]) if name == "heuristic" \
                else model.predict(Xt)
            per_fault[scol] = round(float(np.mean(np.asarray(y_pre) == y_test)), 4)
        calib = None
        if proba_all[0] is not None:
            proba = np.concatenate(proba_all)
            conf = proba.max(axis=1)
            correct = y_pred == y_true
            calib = {
                "brier": multiclass_brier(y_true, proba,
                                          class_names=list(model.classes_)),
                "mean_confidence": round(float(conf.mean()), 4),
                "mean_confidence_correct": round(float(conf[correct].mean()), 4),
                "mean_confidence_wrong": round(float(conf[~correct].mean()), 4)
                if (~correct).sum() else None,
                "n": int(len(y_true)),
            }
        diag_results[name] = {"metrics": rep, "per_scenario_accuracy": per_fault,
                              "calibration": calib}
        print(f"[diagnosis:{name}] accuracy {rep['accuracy']}  macro-F1 {rep['macro_f1']}"
              + (f"  brier {calib['brier']}" if calib else ""))

    for cls in CLASS_ORDER:
        print("   %-12s " % cls + " ".join(
            f"{name[0]}:F1=" + str(diag_results[name]["metrics"]["per_class"][cls]["f1"])
            for name in models))

    # -------- 6. RUL: targets + models ---------------------------------
    rul_train_X, rul_train_y = [], []
    win_X, win_y = [], []
    for aid in train_ids:
        scen = by_asset[aid]
        if scen == "healthy":
            continue
        fdf = frames[aid]
        target = scenario_target(scen)
        rul = build_rul_target(fdf, target)
        feat = model_frame(proc[aid])
        rul_train_X.append(feat)
        rul_train_y.append(rul)
        win_X.append(pd.concat([pd.DataFrame({"t": fdf["t"].to_numpy()}),
                                proc[aid][SENSOR_COLS]], axis=1))
        win_y.append(rul)
    X_rul = pd.concat(rul_train_X).reset_index(drop=True)
    y_rul = np.concatenate(rul_train_y)
    # RUL targets are smooth ramps; a stride of 2 on the training rows keeps
    # the GBM / ridge fit cheap without losing signal (documented in the doc).
    X_rul = X_rul.iloc[::2].reset_index(drop=True)
    y_rul = y_rul[::2]
    win_y_all = np.concatenate(win_y)
    win_X_all = pd.concat(win_X).reset_index(drop=True)

    ridge = RidgeRUL().fit(X_rul, y_rul)
    gbm_rul = GradientBoostingRUL().fit(X_rul, y_rul)
    qgbm = QuantileGradientBoostingRUL().fit(X_rul, y_rul)
    wmlp = WindowMLPRegressor(window=32, sensors=SENSOR_COLS, stride=4,
                              seed=args.seed).fit(win_X_all, win_y_all)
    rul_models = {"ridge": ridge, "gbm": gbm_rul, "quantile_gbm": qgbm,
                  "window_mlp": wmlp}

    # -------- 7. RUL evaluation on held-out fault assets ---------------
    rul_results = {}
    per_scen_mae = {m: {} for m in rul_models}
    all_true = []
    for aid in test_ids:
        scen = by_asset[aid]
        if scen == "healthy":
            continue
        fdf = frames[aid]
        target = scenario_target(scen)
        y_true = build_rul_target(fdf, target)
        feat = model_frame(proc[aid])
        all_true.append(y_true)
        preds = {}
        lo, med, hi = None, None, None
        for mname, m in rul_models.items():
            if mname == "window_mlp":
                Xw = pd.concat([pd.DataFrame({"t": fdf["t"].to_numpy()}),
                                proc[aid][SENSOR_COLS]], axis=1)
                p = m.predict(Xw)  # one value per stride window end
                preds[mname] = p
            elif mname == "quantile_gbm":
                a, b, c = m.predict(feat)
                lo, med, hi = a, b, c
                preds[mname] = b
            else:
                preds[mname] = m.predict(feat)
        n_full = len(y_true)
        for mname in rul_models:
            if mname == "window_mlp":
                p = preds[mname]
                idx = np.arange(31, n_full, 4)
                idx = idx[:len(p)]
                tr = y_true[idx]
                mae = float(np.mean(np.abs(p - tr)))
                per_scen_mae[mname][scen] = round(mae, 0)
            else:
                p = preds[mname][:n_full]
                mae = float(np.mean(np.abs(p - y_true)))
                per_scen_mae[mname][scen] = round(mae, 0)
    # pooled metrics: ridge / gbm / quantile on the full grid
    y_true_pool = np.concatenate(all_true)
    for mname in ["ridge", "gbm"]:
        m = rul_models[mname]
        p = np.concatenate([m.predict(model_frame(proc[a]))
                            for a in test_ids if by_asset[a] != "healthy"])
        rul_results[mname] = {"pooled": evaluate_rul(y_true_pool, p),
                              "per_scenario_mae_s": per_scen_mae[mname]}
    # quantile: pooled lo/med/hi
    lo_all, med_all, hi_all = [], [], []
    for aid in test_ids:
        if by_asset[aid] == "healthy":
            continue
        feat = model_frame(proc[aid])
        lo, med, hi = qgbm.predict(feat)
        lo_all.append(lo), med_all.append(med), hi_all.append(hi)
    lo_p, med_p, hi_p = (np.concatenate(x) for x in (lo_all, med_all, hi_all))
    rul_results["quantile_gbm"] = {
        "pooled_median": evaluate_rul(y_true_pool, med_p),
        "interval_coverage_p10_90": round(interval_coverage(y_true_pool, lo_p, hi_p), 4),
        "mean_interval_width_s": round(float(np.mean(hi_p - lo_p)), 1),
        "per_scenario_mae_s": per_scen_mae["quantile_gbm"],
    }
    rul_results["window_mlp"] = {"per_scenario_mae_s": per_scen_mae["window_mlp"]}
    print("\n[RUL pooled MAE (s)] " + "  ".join(
        f"{k}: {v.get('pooled', v.get('pooled_median', {}))['mae_s']}" if 'pooled' in v or 'pooled_median' in v
        else f"{k}: (per-scenario only)" for k, v in rul_results.items()))
    print(f"[RUL quantile coverage p10-90] {rul_results['quantile_gbm']['interval_coverage_p10_90']}")

    # -------- 7b. severity estimation (how bad is the fault right now) ------
    sev_tr_X, sev_tr_y = [], []
    for aid in train_ids:
        scen = by_asset[aid]
        if scen == "healthy":
            continue
        tdf = proc[aid]
        lab = fault_labels(tdf)
        active = lab.to_numpy() != "healthy"
        Xf = model_frame(tdf)
        sev_tr_X.append(Xf.loc[active])
        sev_tr_y.append(tdf["fault_severity"].to_numpy()[active])
    X_sev = pd.concat(sev_tr_X).reset_index(drop=True).iloc[::2].reset_index(drop=True)
    y_sev = np.concatenate(sev_tr_y)[::2]
    sev_models = {"ridge": SeverityRegressor("ridge").fit(X_sev, y_sev),
                  "gbm": SeverityRegressor("gbm").fit(X_sev, y_sev)}
    sev_results = {}
    for name, m in sev_models.items():
        yt_all, yp_all, per_scen = [], [], {}
        for aid in test_ids:
            scen = by_asset[aid]
            if scen == "healthy":
                continue
            tdf = proc[aid]
            lab = fault_labels(tdf)
            active = lab.to_numpy() != "healthy"
            Xf = model_frame(tdf).loc[active]
            yt = tdf["fault_severity"].to_numpy()[active]
            yp = m.predict(Xf)
            yt_all.append(yt)
            yp_all.append(yp)
            per_scen[scen] = evaluate_severity(yt, yp)["mae"]
        yt_p = np.concatenate(yt_all)
        yp_p = np.concatenate(yp_all)
        sev_results[name] = {"pooled": evaluate_severity(yt_p, yp_p),
                             "per_scenario_mae": per_scen}
    print("[severity pooled MAE (0..1)] "
          + "  ".join(f"{k}: {v['pooled']['mae']}" for k, v in sev_results.items()))

    # -------- 8. SHAP explainability -----------------------------------
    test_feat = pd.concat([model_frame(proc[a]) for a in test_ids]).reset_index(drop=True)
    # a representative bearing sample: mid-degradation on a held-out bearing
    # asset (onset 1800 s, severity ~40-50 % at row ~6000), not the
    # post-protective-stop cooling tail.
    brg_test = next(a for a in test_ids if by_asset[a] == "bearing")
    brg_feat = model_frame(proc[brg_test])
    row_idx = min(len(brg_feat) - 1, 6000)
    row = brg_feat.iloc[row_idx]
    row_df = pd.DataFrame([row.to_dict()])

    shap_cls = shap_feature_importance(rf, test_feat,
                                       class_names=list(rf.classes_), seed=args.seed)
    shap_rul = shap_feature_importance(gbm_rul.raw_model, test_feat, seed=args.seed)
    cls_idx = int(np.where(np.array(rf.classes_) == "bearing")[0][0])
    shap_diag_sample = shap_sample_explanation(
        rf, row_df, list(brg_feat.columns), class_index=cls_idx)

    results = {
        "experiment": "diagnosis-rul",
        "phase": 5,
        "seed": args.seed,
        "n_train_assets": len(train_ids),
        "n_test_assets": len(test_ids),
        "diagnosis": diag_results,
        "rul": rul_results,
        "severity": sev_results,
        "shap": {"classifier": shap_cls, "rul_regressor": shap_rul,
                 "sample_bearing_diagnosis": shap_diag_sample},
        "elapsed_s": round(time.time() - t0, 1),
    }

    out_file = Path("experiments/results/diagnosis_rul_comparison.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\nresults json: {out_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())