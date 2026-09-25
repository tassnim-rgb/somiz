# Fault diagnosis + Remaining Useful Life + explainability (Phase 5)

Scope of this document:

1. **Fault diagnosis** - which failure mode is acting on an asset
   (bearing wear, cooling / overheating, seal leakage, impeller erosion,
   discharge blockage, or healthy), with class probabilities (calibration
   checked via Brier score) and a severity estimate (0..1).
2. **Remaining Useful Life (RUL)** - time to the asset's intervention
   threshold, with quantile prediction intervals as an uncertainty estimate.
3. **Explainability** - SHAP (TreeExplainer) attributions for the diagnosis
   and RUL models.

Everything here is SIMULATED: the ground truth comes from the physics twin
(`simulation/`), and all numbers in this document are MODEL ASSUMPTION and
SIMULATED RESULTS unless explicitly stated otherwise. There is no real-plant
telemetry anywhere in this project.

Run the experiment with:

```bash
python scripts/run_diagnosis_experiment.py --seed 42 --n-per-scenario 3
```

Results are written to `experiments/results/diagnosis_rul_comparison.json`.

---

## 1. Problem framing

### 1.1 Diagnosis labels (ground truth)

Each sample is labelled by `ml.diagnosis.fault_labels()`:

- `healthy` if `fault_severity < 0.05` (the simulator's EARLY-stage
  onset threshold), whatever the "dominant_fault" field says;
- otherwise the active `dominant_fault`.

Six classes: `healthy`, `bearing`, `overheating`, `leakage`, `impeller`,
`blockage`. The catalog scenarios are single-fault; a multi-fault asset is
labelled by its dominant (highest severity) fault. The dominant fault is
fully determined by the simulator's FaultSpec, so the labels are exact by
construction - a property of the SIM, not of a real plant.

### 1.2 The reference: a rule-based classifier (no ML)

`HeuristicFaultClassifier` is the honest "before machine learning" bar. It
needs only a steady-state healthy reference (per-sensor mean / std of the
first part of a healthy qualification run) and documents the physics
signatures it uses:

| fault       | signature rule (z-score vs healthy reference)          |
|-------------|---------------------------------------------------------|
| overheating | `t_motor >= 2.5` (checked first, see below)             |
| bearing     | `vib >= 3.0`                                            |
| blockage    | `p_disch >= 3.0` and `flow <= -2.0`                     |
| impeller    | `efficiency <= -3.0`                                    |
| leakage     | `flow <= -2.0` and `p_disch <= -2.0`                    |

Rules apply in order, first match wins for each sample. The ordering is
physics-justified: in the SIM, the overheating fault raises motor
temperature *slowly* (long thermal time constant) but also perturbs
vibration strongly, so a vibration-only rule confuses it with bearing wear.
The temperature channel is therefore checked first (with a lower threshold);
it is the specific discriminator (see section 4 for the measured weakness
of this reference).

### 1.3 Supervised models

All trained on the same processed feature frames (`pipeline/`):
z-scored sensors + trailing 60 s rolling mean/std + rate-of-change
(`_delta`, `_delta_abs`), scaler fitted on training assets only.

- Random Forest (class-balanced);
- Gradient Boosting (class-balanced via sample weights);
- MLP (sklearn, early stopping on a 25 k-row training subsample);

compared in a table with the rule reference, plus:

- per-class precision / recall / F1 and support;
- macro-F1 (mean of per-class F1), weighted-F1, accuracy;
- confusion counts (classes x classes);
- per-scenario held-out accuracy;
- calibration: multi-class Brier score, mean predicted-class confidence,
  and confidence separated into correct vs wrong predictions (an honest
  check of whether the probability output can be trusted in the UI).

### 1.4 Severity estimation

`SeverityRegressor` predicts how bad the active fault is right now (0..1),
trained on fault-active samples only (targets = SIMULATED
`fault_severity`). Ridge (linear baseline) and gradient boosting; evaluated
by MAE/RMSE/bias on held-out assets, pooled and per scenario. This is the
`severity_estimate` field of the (planned Phase 7) diagnoses table.

### 1.5 Evaluation protocol (no leakage)

Assets are split **by repeat**, not by rows: for each scenario, the first
`n-1` generated assets are training, the last one is held out untouched.
The scaler is fitted on a training healthy asset only. All metrics are
computed on the held-out assets. This measures the deployment-relevant
question: does the model work on machines it has never seen?

The healthy class is subsampled in training (documented cap per asset) so
the minority fault classes are not drowned out; evaluation keeps the real
class proportions.

---

## 2. Remaining Useful Life

### 2.1 Definition (SIMULATED ground truth)

For each failure mode, the intervention threshold is 95 % of the scenario's
target severity (`SCENARIOS[<mode>][0].target`), e.g.:

| scenario     | target severity | intervention threshold (95 %) |
|--------------|-----------------|-------------------------------|
| bearing      | 1.00            | 0.950                         |
| overheating  | 0.90            | 0.855                         |
| leakage      | 0.80            | 0.760                         |
| impeller     | 0.70            | 0.665                         |
| blockage     | 0.70            | 0.665                         |

RUL(t) = max(0, t_fail - t) where t_fail is the first time the severity
crosses the threshold, capped at 3 h (10800 s). A scenario that never
reaches its threshold in the run is *censored* and its RUL is flat at the
cap for the whole run (the machine is not progressing towards the
intervention point).

Two deliberate modelling choices (both documented in the artefacts):

- the per-mode threshold is intentional: an impeller at 70 % damage never
  reaches severity 1.0, but it still has a defined intervention point;
- in a real deployment the label source is the reliability engineer's
  maintenance threshold, not the SIM - **this twin's RUL labels are
  simulated ground truth and no claim is made about real plants**.

### 2.2 Models

| model             | family          | input                                  |
|-------------------|-----------------|----------------------------------------|
| Ridge             | linear baseline | current features (z-scored + rolling)  |
| GradientBoosting  | classical       | current features                       |
| Quantile GBM      | uncertainty     | features, p10 / p50 / p90 GBMs         |
| Windowed MLP      | temporal        | trailing 32-sample window of z-scored sensor channels (PyTorch) |

Training rows are stride-2 subsampled (RUL targets are smooth ramps, so this
costs nothing) and window MLP windows stride 4; both documented in code.
The windowed MLP is strictly causal: a window only sees its trailing
samples, and windows never straddle assets (segments split at `t` resets).

Note: `t` (asset age) is deliberately NOT a feature. The models must read
RUL from the sensor signals, not from a clock - the deployment-grade
question. Assets age monotonically in the fleet and a timer-based model
would look perfect in this SIM and fail on any real asset.

### 2.3 Evaluation

- pooled MAE / RMSE over the held-out fault assets;
- per-scenario MAE;
- interval coverage: fraction of true RUL inside the p10-p90 band (an
  honest calibration check, never assumed);
- mean interval width (how informative the uncertainty is).

---

## 3. Explainability (SHAP)

`ml/explain.py` wraps `shap.TreeExplainer` (an exact, game-theoretic
attribution for tree ensembles) with serialisable outputs:

- **global** mean |SHAP| per feature, per class for the RF classifier and
  per-output for the mean-GBM RUL model;
- **per-sample** attributions for one mid-life bearing case (diagnosis
  class logit and RUL prediction), for the narrative in the report.

The wrapper normalises the different shapes `shap` returns across versions
(list of per-class arrays vs `(samples, features, classes)` ndarray).

Limitations stated here so they are not forgotten in the PR: SHAP explains
the *model*, not the physics. A model trained on the SIM can only attribute
signals the SIM generates; the attributions are a debugging / trust aid.
The conclusions one can draw are "the model leans on vibration for bearing
wear", not "bearings are diagnosed by vibration in real plants".

---

## 4. Results (seed 42, 3 assets per scenario, 6 h runs)

Fleet: 18 assets - 3 healthy + 3 x (bearing, overheating, leakage,
impeller, blockage). Held out: 1 asset per scenario (5 fault + 1 healthy).

### 4.1 Diagnosis

| method           | accuracy | macro-F1 | Brier | conf (corr/wrong) | best class (F1)  | worst class (F1)            |
|------------------|----------|----------|-------|-------------------|------------------|-----------------------------|
| heuristic (no ML)| 0.4147   | 0.3142   |  -    |  -                | healthy 0.7907   | 0.0 (leakage/impeller/blockage) |
| random forest    | 0.9994   | 0.9995   | 0.00172 | 99.4 / 58.8      | impeller 1.0000  | healthy 0.9988              |
| gradient boost   | 0.9993   | 0.9994   | 0.00114 | 99.99 / 89.7     | blockage 0.9998  | healthy 0.9985              |
| MLP              | 0.9976   | 0.9978   | 0.00366 | 99.7 / 67.9      | bearing 0.9990   | healthy 0.9946              |

Per-class precision / recall / F1, held-out per-scenario accuracy and the
severity estimation table are in the results JSON.

**Measured failure mode of the rule reference.** On the held-out assets the
healthy-machine vibration is nearly constant in the SIM (std ~ 0.04 on a
~ 0.8 mean), so the bearing gate `vib >= 3.0` is crossed by 93-100 % of the
fault-active samples of leakage, impeller, blockage and overheating. Since
the bearing rule is checked *before* the blockage / impeller / leakage
rules, those classes collapse into "bearing" (their F1 is exactly 0.0). The
overheating gate (`t_motor >= 2.5`, checked first) still captures 78.6 % of
overheating, and only the healthy default and the temperature gate
survive: healthy F1 0.79, overheating F1 0.89, everything else 0. Bearing
itself is only 44 % above the gate (its vibration ramp is slow), so half
its samples fall through to "healthy". The ML models read the full feature
frame (temperature, flow, pressure, efficiency channels) and separate all
six classes essentially perfectly, which is what the feature attribution
in section 4.4 shows they are actually doing.

### 4.2 Severity estimation (0..1)

| method | pooled MAE | pooled RMSE | bias    |
|--------|------------|-------------|---------|
| Ridge  | 0.0179     | 0.0262      | -0.0006 |
| GBM    | 0.0021     | 0.0045      | -0.0001 |

Both regressors are trained and evaluated on fault-active samples only;
per-scenario MAE is in the JSON (worst case: impeller ridge 0.0423, all
GBM per-scenario MAEs <= 0.0031).

### 4.3 RUL

| model            | pooled MAE (s) | per-scenario MAE (s) (bearing / overheating / leakage / impeller / blockage) | interval coverage | mean width |
|------------------|----------------|--------------------------------------------------------------------------------|-------------------|------------|
| Ridge            | 716.4          | 262 / 828 / 359 / 1386 / 748                                                |   -               |  -         |
| GradientBoosting | 273.3          | 69 / 325 / 276 / 392 / 306                                                   |   -               |  -         |
| Quantile GBM     | 277.7 (median) | 98 / 388 / 233 / 383 / 287                                                   | 0.9053            | 3388 s     |
| Windowed MLP     |  -              | 71 / 434 / 267 / 423 / 356                                                   |   -               |  -         |

> The windowed MLP predicts at window ends (one value per stride step), so
> its evaluation is aligned on the same grid; pooled metrics are reported
> for the full-grid models only.

### 4.4 SHAP highlights (measured, 300-sample background)

- **RF diagnosis - top drivers per fault class** (mean |SHAP|):
  - bearing: efficiency, rpm, power;
  - overheating: t_motor, vibration, flow;
  - leakage: flow, p_disch;
  - impeller: power, rpm, p_disch;
  - blockage: p_disch, flow.
  The attributions match the SIM's physics signatures (section 1.2): the
  temperature channel drives overheating, flow/pressure drive
  leakage/blockage, efficiency/rpm drive bearing/impeller wear.
- **RUL (mean GBM) - top drivers**: vibration (mean |SHAP| ~ 2071 s), flow
  (~ 827 s), motor temperature (~ 724 s), then flow/power/current means.
  Vibration dominates because the bearing mode has both the largest
  excursion and the longest RUL ramp in the pooled test set.
- **Bearing sample at mid-life**: efficiency, rpm and pressure all push the
  "bearing" class logit up (efficiency mean +0.158, efficiency +0.148,
  rpm +0.090) - consistent with the efficiency-degradation signature the
  SIM gives to bearing wear.

---

## 5. Known limitations (honest list)

1. **Simulated everything.** Labels, RUL targets, thresholds and "plants"
   come from the twin; absolute numbers transfer to the real world only
   after re-running this pipeline on real fleet data.
2. **The rule reference is deliberately naive**; it is included to show
   what "no ML" looks like rather than as a deployment candidate.
3. **Single-fault catalog**: trained and evaluated on single-fault runs.
   Compound faults (e.g. bearing + leakage) are out of scope for Phase 5
   and would need multi-fault data.
4. **RUL per-mode thresholds are assumptions**, not engineering standards.
5. **Windowed MLP is the heaviest model** and its CPU training is not
   bitwise-deterministic across machines (distribution is reproducible via
   seeds); inference on a fitted model is deterministic.
   It accepts a `device` parameter (`auto` / `cpu` / `cuda`); on this
   machine `auto` resolves to CPU and the CUDA branch is untested here.
6. **SHAP explains the SIM-trained model**, not the physics of a real pump.

## 6. Files

- `ml/diagnosis.py` - labels, rule reference, classification metrics,
  severity regressor, Brier-score calibration
- `ml/rul.py` - RUL targets, models (ridge / GBM / quantile GBM /
  windowed MLP, shared training loop)
- `ml/explain.py` - SHAP wrappers
- `scripts/run_diagnosis_experiment.py` - the Phase 5 experiment
- `tests/test_diagnosis.py`, `tests/test_rul.py`, `tests/test_explain.py`
- `experiments/results/diagnosis_rul_comparison.json` - results artefact