# Anomaly Detection (Phase 4)

Unsupervised detection of "this machine is not behaving like its healthy
self" from sensor streams. Four methods are implemented behind one interface
(`ml/anomaly.py`) and compared with industrial metrics (`ml/evaluate.py`).

## The four detectors

| Method | Class | Idea | Cost / interpretability |
|--------|-------|------|--------------------------|
| Statistical baseline | `StatisticalBaselineDetector` | workhorse control chart: persistent RMS z-score of standardised sensors against a healthy reference | cheapest, fully explainable |
| Isolation forest | `IsolationForestDetector` | tree-ensemble isolation on the feature frame (rolling statistics included) | baseline-vs-complexity method |
| Autoencoder | `PointAutoencoderDetector` | PyTorch undercomplete autoencoder on standardised sensor vectors; score = reconstruction error | captures sensor correlations |
| Temporal autoencoder | `WindowedAutoencoderDetector` | same, but on sliding windows of 32 consecutive samples (learns temporal structure); score per window at its end sample | most expressive (deep learning) |

All detectors are **trained on healthy data only, with no anomaly labels
(truly unsupervised)** and return a per-sample anomaly score (higher = more
anomalous). Thresholding, debouncing and evaluation live in
`ml/evaluate.py`.

## Metrics that matter to a maintenance engineer

- **Precision / recall / F1** and **AUC / PR-AUC**: standard ranking quality.
- **False alarm rate (FAR)**: fraction of healthy samples flagged, also
  expressed **per day**. A model that finds every fault but screams 5,000
  times a day gets ignored by operators.
- **Detection delay**: seconds from the true fault onset to the first
  *sustained* alarm (see debouncing below). Reported per fault asset and at
  matched operating points.
- **Operating-point selection**: a `threshold_sweep` walks the whole
  trade-off curve. Two honest ways to pick a point:
  - best F1 (`best_by_f1`), or
  - highest recall among thresholds whose FAR stays under a budget
    (`at_far_target`, e.g. FAR <= 2%).

### Debouncing

Raw per-sample flags are too noisy to act on. `persist_flags(flags, k=3)`
turns an alarm on only when at least 3 of the last 3 samples are flagged.
This is the standard industrial answer to single-sample spikes; it also
shifts detection delay by `k-1` samples, which the delayed-detection unit
tests verify explicitly.

## Experiment results (seed 42, 6 h per asset)

Pooled over 3 healthy eval runs + bearing / overheating / leakage runs
(`python scripts/run_anomaly_experiment.py`):

| Method | AUC | PR-AUC | F1 | P | R | FAR | FAR/day | delay (s) | delay @ FAR<=2 % |
|--------|-----|--------|----|----|----|-----|---------|-----------|------------------|
| statistical | 0.997 | 0.997 | 0.979 | 1.0 | 0.975 | 0.025 | 3692 | 0 | 31 |
| isolation_forest | 0.862 | 0.900 | 0.858 | 0.8 | 0.924 | 0.345 | 50108 | 0 | 0 |
| point_ae | 0.992 | 0.996 | 0.932 | 1.0 | 0.874 | 0.000 | 20 | 871 | 871 |
| windowed_ae | 0.998 | 0.998 | 0.904 | 1.0 | 0.827 | 0.003 | 400 | 991 | 991 |

Per-fault-asset detection delay at each method's pooled best-F1 threshold:

| Method | BRG-01 | OVH-01 | LEK-01 |
|--------|--------|--------|--------|
| statistical | 0 s | 736 s | 523 s |
| isolation_forest | 0 s | 0 s | 0 s |
| point_ae | 871 s | 3190 s | 1897 s |
| windowed_ae | 991 s | 4271 s | 4145 s |

### Reading the table honestly

- The **statistical baseline wins on F1** (0.979) with zero best-case delay,
  but at that operating point it raises 3,692 alarms/day (FAR 2.5 %). At a
  FAR <= 2 % budget its delay is 31 s. On simulated data the control chart is
  hard to beat: the physics produces strong, smooth signal deviations.
- **Isolation forest** is the weakest here (FAR 34.5 % at best F1): the
  healthy region is not an easily-isolable blob once rolling features of
  smooth signals are included, and contamination priors do not match this
  data.
- The **autoencoders are the most conservative** (FAR 0.0-0.4 % = 8-400
  alarms/day) and trade speed for calm: detection delay of 15-70 minutes.
  Their PR-AUC ties the statistical model, meaning the ranking is just as
  good once the threshold is raised.
- **Delay and FAR are a trade-off, not a bug**: this comparison exists so a
  deployment can pick the operating point by acceptable false-alarm budget,
  which is the honest way to compare methods.

All numbers are SIMULATED on the digital twin (accelerated degradation,
documented in `docs/MATHEMATICAL_MODEL.md`); they demonstrate method ranking
and evaluation methodology, not real-plant performance.

## Reproducibility

- Dataset: deterministic `DatasetGenerator(master_seed=42)`; provenance in
  `data/generated/anomaly_experiment/manifest.json`.
- Detectors train on healthy fit data only (first 60 % of each healthy
  asset); healthy evaluation uses only the never-seen 40 % tail.
- Ground-truth columns never reach detectors (`model_frame` keeps sensors +
  derived features, drops `health_stage`, `fault_severity`, `d_*`,
  `anomaly_target`).
- Results JSON: `experiments/results/anomaly_comparison.json`.
- Results on healthy / fault assets show NaN handling for the constant
  ground truth (`r(severity)` is n/a when severity never moves).