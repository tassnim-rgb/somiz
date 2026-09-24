# Health Index (Phase 4)

The health index (`digital_twin/health_index.py`) is a 0-100, higher-is-better
per-sample score that answers one question for a maintenance engineer:

> How far is this machine living from its own healthy behaviour, right now?

It is computed from **observed sensor data only**. Ground-truth labels
(`fault_severity`, `health_stage`, `d_*`) are used solely for validation and
are never part of the formula (no label leakage).

## Formula

1. **Commissioning reference curve** `ref_s(t)` per sensor `s`, fitted on an
   observed, label-free healthy qualification run of the same machine type and
   load profile:

   - take the steady-state part of the healthy pool, `t >= warmup_s`;
   - per-time mean over the healthy pool (all healthy assets share the time
     grid), smoothed with a centred rolling window (`ref_smooth_s`).

   The reference is *time-indexed* deliberately. A motor-driven pump has a slow
   thermal soak after start-up (tirelessly climbing 26 C to 49 C over two hours
   in simulation). A static mean reference would misread any warm healthy
   machine as degraded; the commissioning curve absorbs such normal dynamics.

2. **Standardised residual**

   ```
   z_s(t) = ( x_s(t) - ref_s(t) ) / sigma_s
   ```

   where `sigma_s` is the residual standard deviation of the healthy pool
   around the reference. Sensor dropouts (NaN telemetry) are left as missing:
   the row is reported as `NO_READING`, never fabricated.

3. **Noise damping**: `z_s` is smoothed with a trailing window (`window`, 60 s
   by default) so a single noisy sample cannot move the index.

4. **Composite deviation**

   ```
   D(t) = sqrt( sum_s w_s * z_s(t)^2 / sum_s w_s )
   ```

   with documented default weights: vib 1.5 (bearing signature), t_motor 1.0,
   efficiency 1.0, current 0.8, flow 0.6, p_disch 0.6, t_fluid 0.4, rpm 0.4.
   The weights are a configurable engineering prior, not fitted.

5. **Health index**

   ```
   HI(t) = 100 * exp( -D(t) / tau ),   tau = 2
   ```

   A smooth, monotonic map: D = 0 gives 100; D >> tau drives HI toward 0.

### Explainability

`evaluate()` returns, per row, the per-sensor smoothed deviations `wz_<sensor>`
and `top_signals`: the three sensors with the largest weighted |z|, so an
analyst can see *why* the index moved ("vib+t_motor+efficiency").

## Operational semantics

- `t < warmup_s` (default 120 s): start-up transient. The index is **not
  defined** (stage `WARMUP`, HI = NaN). Coupled with the commissioning
  reference this removes the so-called "healthy false alarm" seen with static
  baselines during soak.
- Beyond the reference horizon the last reference value is extrapolated (the
  machine is assumed at steady state). Documented model assumption.
- Sensor dropout: stage `NO_READING`, HI = NaN. The pipeline's imputation
  step is the production path for filling dropouts; the index itself never
  invents readings.

## A-priori bands (not fitted)

| Bands    | Range   |
|----------|---------|
| NORMAL   | 80-100  |
| EARLY    | 60-80   |
| MODERATE | 40-60   |
| SEVERE   | 20-40   |
| FAILURE  | 0-20    |

These are declared engineering thresholds. Validation against the simulator
ground truth checks whether they behave sensibly; it does not tune them.

## Validation result (seed 42, 6 h per asset)

`scripts/run_anomaly_experiment.py` fits the index on three healthy 6 h runs
and evaluates it on those plus bearing / overheating / leakage runs:

| Asset  | HI mean | HI min | r(severity) | Stage alignment |
|--------|---------|--------|-------------|-----------------|
| HLT-01 | 93.9    | 30.4   | n/a (sick=0)| 0.994           |
| HLT-02 | 93.8    | 30.1   | n/a          | 0.994           |
| HLT-03 | 94.0    | 32.6   | n/a          | 0.993           |
| BRG-01 | 8.4     | 0.0    | -0.633       | 0.621           |
| OVH-01 | 18.7    | 0.0    | -0.883       | 0.731           |
| LEK-01 | 19.7    | 0.0    | -0.832       | 0.168           |

- Healthy machines sit in NORMAL (mean ~94) with 99.4 % band/stage agreement;
  the minimum dips to ~30 come from the smoothing ramp at the edge of the
  warm-up window in these runs and are not failures.
- Faulted machines collapse toward FAILURE and correlate strongly and
  negatively with true severity (r from -0.63 to -0.88).
- Leakage shows the weakest band alignment: it manifests as flow/efficiency
  losses that move the index in a different part of the scale than the
  stage thresholds. This is exactly what Phase 5 (fault diagnosis) must
  separate; the index measures *how sick*, not *what sickness*.

All numbers are SIMULATED. They validate the maths on the twin; they are not
claims about any real deployment.