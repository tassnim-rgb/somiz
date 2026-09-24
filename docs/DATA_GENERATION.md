# Data Generation & Preprocessing

**Status:** SIMULATED DATA ONLY (until a real telemetry bridge is connected)

This document specifies (1) how reproducible synthetic datasets are produced
from the digital twin and (2) every transformation the preprocessing pipeline
applies to them — with the anti-leakage policy made explicit. It is the
contract referenced by `pipeline/preprocess.py` and `dataengine/`.

---

## 1. Dataset generation (`dataengine/`)

### 1.1 Reproducibility

A dataset is fully determined by `(master_seed, asset specs)`:

- Each asset receives `seed = master_seed + index * 7919` (a prime stride so
  nearby assets do not correlate), which seeds **one** NumPy Generator that
  drives physics-free stochasticity (sensor noise, missing samples,
  outliers). The physics integration itself is deterministic.
- The same generator call therefore produces **bit-identical files**, which
  is verified by `test_generation_is_deterministic` (SHA-256 equality).

### 1.2 Scenario catalogue (`dataengine.SCENARIOS`)

| Scenario | Fault(s) | Onset | Target | Duration |
|---|---|---|---|---|
| `healthy` | none | – | – | – |
| `bearing` | bearing wear | 1800 s | 1.00 (FAILURE) | 9000 s |
| `overheating` | motor cooling loss | 3600 s | 0.90 | 6000 s |
| `leakage` | internal recirculation | 3600 s | 0.80 | 9000 s |
| `impeller` | impeller erosion | 3600 s | 0.70 | 12000 s |
| `blockage` | partial discharge blockage | 2400 s | 0.70 | 6000 s |

Defaults assume a 6-hour run at 1 Hz (21 601 samples). Shorter runs must
shorten fault timelines (override via `AssetRunSpec.faults`), otherwise the
scenario does not progress within the window — an explicit, tested behaviour.

### 1.3 Manifest (provenance)

`manifest.json` records, per asset: `asset_id`, `scenario`, `seed`,
`n_samples`, file names, **SHA-256 of the primary export**, and the complete
simulation config (machine parameters, profile, faults, sensor configs). Top
level: `master_seed`, `generated_utc`, `schema_version`, `simulator_model`.
Any figure or metric can therefore be traced back to its generating
assumptions — nothing is anonymous.

### 1.4 CLI

```bash
python scripts/generate_dataset.py --seed 42 --outdir data/generated \
    --assets 4 --duration 21600 --fs 1 --format csv,parquet
python scripts/generate_dataset.py --scenario bearing --assets 1 --duration 3600
```

Exports: CSV (human-readable, always available) and Parquet (columnar,
requires `pyarrow`). Generated data lives under `data/generated/` and is
**gitignored** — datasets are re-creatable from the manifest.

---

## 2. Preprocessing (`pipeline/`)

### 2.1 Order of operations

```
1. validate      schema, monotonic time, plausible ranges, NaN census
2. impute        fit-free interpolation (linear / ffill / none)
3. split         chronological (fit | validation | test), never shuffled
4. fit scaler    normalisation statistics from FIT SLICE ONLY
5. transform     apply that scaler to all three slices
6. features      trailing rolling stats + rate of change
7. spectral      optional per-window FFT features (post-split)
```

`Preprocessor.transform_log` records each applied step, and
`ValidationReport` records issues + NaN counts — both are surfaced in
`Preprocessor.report()` so a run can never silently change meaning.

### 2.2 Validation rules

| Check | Failure |
|---|---|
| required columns present (`t`, 9 sensors, `health_stage`, `fault_severity`, `dominant_fault`) | hard error |
| `t` strictly increasing, no duplicates | hard error |
| sensor values within `RANGE_BOUNDS` | hard error (issues listed) |
| NaN census per column | reported (not fatal; imputation handles) |

`RANGE_BOUNDS` are generic engineering bounds for the default pump archetype
(in `pipeline/schema.py`); a real deployment must override them per asset.

### 2.3 Imputation

- `linear` (default): linear interpolation between neighbours; leading/trailing
  NaNs filled from the nearest valid value (direction-limited, no future
  beyond the gap).
- `ffill`: forward-fill then back-fill leading NaNs.
- `none`: keep NaN (for consumers that handle it themselves).

### 2.4 Normalisation

Fitted **on the fit slice only** and then applied unchanged to val/test:

| Mode | Statistic | Fit slice property |
|---|---|---|
| `zscore` (default) | mean, std (ddof=1) | mean ≈ 0, std = 1 |
| `robust` | median, IQR (10–90%) | median ≈ 0 |
| `minmax` | min, max | range = [0, 1] |
| `none` | – | – |

Constant columns are detected at fit time and excluded (zero variance —
standardising them would divide by zero).

### 2.5 Features

- **Rolling** (`rolling_window`, default 60 samples): trailing mean, std,
  min, max, median. Windows are **shifted by one row**, so the feature at
  time *t* depends strictly on samples *< t* — verified numerically by
  `test_leakage_guard_order_preserved`.
- **Rate of change**: first difference and absolute first difference per
  sensor.
- **Spectral** (optional, per-window): dominant frequency, spectral centroid,
  low-band (≤25 % Nyquist) energy ratio over contiguous windows. Computed
  **after** the chronological split, each window fully inside one fold —
  windows never straddle train/test.

### 2.6 Targets

`anomaly_target` (binary) = `fault_severity >= anomaly_threshold`
(default 0.05 = the default `EARLY` stage onset). The mapping is one line,
configurable, and logged — never hidden.

---

## 3. Anti-leakage policy (enforced by design + tests)

1. Splits are contiguous in time, never shuffled (`chrono_split` rejects
   unsorted input).
2. Normalisation statistics are fit on the fit slice only; `fit_transform`
   on val/test is impossible without refitting.
3. Rolling features are trailing + shifted; spectral features are per-window
   post-split.
4. `expanding_window_cv` supports a purge `horizon` between train and
   validation for context-window models (standard safeguard).

Tests: `tests/test_pipeline.py` (validation, imputation, fit-on-train-only,
rolling causality, split ordering, purge gaps, spectral units, target),
`tests/test_dataengine.py` (determinism, seed sensitivity, manifest,
round-trips, scenario catalogue, explicit-fault override).

---

## 4. What this data is NOT

- **Not real**: everything above is produced by
  `rotating-machine-lumped-v1` (see `docs/MATHEMATICAL_MODEL.md`).
- **Not calibrated**: no SOMIZ equipment parameters were used; degradation is
  accelerated (hours, not months).
- **No performance claim**: any ML result on this data is a *simulation
  performance* metric, reported separately from real-world validity.
