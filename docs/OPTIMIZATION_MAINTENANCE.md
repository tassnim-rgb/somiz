# Maintenance optimisation: criticality + scheduling (Phase 6)

Scope of this document:

1. **Criticality model** - per asset, a *risk* score
   `P(failure before horizon) x failure cost`, with A/B/C classes and an
   explained breakdown; the input for prioritisation.
2. **Maintenance scheduling** - which assets to maintain on which day over
   a planning horizon, under a daily crew-capacity constraint and
   no-maintenance days (modelled weekends), minimising total cost.
3. **Decision engine** - a small MILP solved by `scipy.optimize.milp`
   (HiGHS, already installed), compared against two honest baselines:
   greedy (risk order, earliest free day) and do nothing.

Every input here is SIMULATED / MODEL ASSUMPTION. The RUL distributions
(days) are planning inputs built from the twin's scenario semantics and
the costs are planner-supplied assumptions; nothing in this package
claims to describe a real plant. Robustness of a schedule to RUL
**estimation error** is explicitly deferred to Phase 9 and *not* claimed
here: the reality check uses the same RUL estimates that drove the plan.

Run the experiment with:

```bash
python scripts/run_optimization_experiment.py --seed 42
```

Results are written to `experiments/results/optimization_comparison.json`.

---

## 1. Criticality model

For each asset the planner provides a RUL distribution (p10 / p50 / p90
quantiles in days, the same shape the Phase 5 quantile GBM produces) and
a failure consequence cost. The failure probability by a horizon `H` is
estimated in quantile space:

- `P(RUL < H)` interpolates linearly through the anchors
  `(p10, 0.10), (p50, 0.50), (p90, 0.90)`, with linear extrapolation
  outside the anchors and clamping to `[0.02, 0.98]`.

This is MODEL ASSUMPTION: a cheap, convenient stand-in for a full
survival model (Weibull-like fitting over planted RUL populations is a
research item, not a Phase 6 claim).

- `risk = P(failure before H) x failure cost`
- class A / B / C = terciles of risk over the fleet (planner-facing
  prioritisation bucket)
- every row carries an `explanation` string with the decomposition, so
  the score is auditable in the (future Phase 8) dashboard.

## 2. Scheduling formulation (MILP)

Decision variables `x(i,d) in {0,1}`: "maintain asset i on day d" for
`d = 0..H-1`, plus a dummy action `d = H` meaning "no maintenance".

Per-asset cost matrix `c(i,d)`:

| action                                      | cost |
|---------------------------------------------|------|
| day `d < floor(p50 RUL)` (preventive window) | planned maintenance cost |
| day `d >= floor(p50 RUL)` (too late)         | planned + failure cost (reactive) |
| no maintenance, p50 RUL < H                 | expected failure cost |
| no maintenance, p50 RUL >= H                | 0 |

Objective: minimise total cost. Constraints:

- exactly one action per asset (maintain on a day, or decide not to);
- per-day crew capacity: `sum_i x(i,d) <= cap` (a modelled weekend is
  `cap = 0` on the configured window days).

Solved with `scipy.optimize.milp` (HiGHS). **CVXPY** remains the
documented upgrade path for larger / convex-differentiable formulations
(e.g. non-linear maintenance-cost curves); it is commented out in
`requirements.txt` exactly because the current MILP needs no extra
dependency.

## 3. Baselines (honest comparison)

- **greedy**: sort by risk (criticality report), highest first; assign
  each asset the earliest day with free crew capacity, preventive window
  preferred. It does not weigh the cost of an unnecessary intervention.
- **do nothing**: pay every in-horizon failure.

The experiment compares the three policies under crew capacities of
2, 3 and 5 per day on the same 18-asset fleet (deterministic seed).

---

## 4. Results (seed 42, 18 assets, 14-day horizon, window days 5 and 12)

Fleet: 18 planning assets, RUL(p50) spread 1.2..34 days, failure costs
60k..650k EUR (mission-critical assets cost more), planned maintenance
= 15 % of failure cost (MODEL ASSUMPTION).

### 4.1 Headline (capacity 3/day)

| policy      | total cost (EUR) | failures | planned | reactive |
|-------------|------------------|----------|---------|----------|
| MILP        | 211 127          | 0        | 5       | 0        |
| greedy      | 589 332          | 0        | 18      | 0        |
| do nothing  | 1 407 510        | 5        | 0       | 0        |

MILP saves **64.2 %** vs the greedy baseline and **85.0 %** vs doing
nothing.

Why the greedy gap is so large (measured, not hand-waved): the greedy
rule maintains every asset in risk order on the first free day, so it
spends 18 planned interventions even on assets whose RUL p50 (up to
34 days) outlives the 14-day horizon. The MILP treats "do nothing" as a
costed alternative and only intervenes on the 5 assets whose failures
are expected inside the horizon. There is no oracle in either policy:
both use the same (SIMULATED) RUL estimates.

### 4.2 Crew-capacity scenarios

| capacity | MILP (EUR) | greedy (EUR) | do nothing (EUR) | MILP vs greedy |
|----------|------------|--------------|------------------|----------------|
| 2/day    | 211 127    | 589 332      | 1 407 510        | -64.2 %        |
| 3/day    | 211 127    | 589 332      | 1 407 510        | -64.2 %        |
| 5/day    | 211 127    | 589 332      | 1 407 510        | -64.2 %        |

Honest note: with this RUL spread only 5 assets need maintenance in the
horizon, so the crew constraint is not binding at any tested capacity;
the scenario grid documents that the savings are resource-independent
here. A binding-capacity stress case (more near-end-of-life assets) is
easy to run with the same script by changing the RUL spread.

### 4.3 Criticality (top of the fleet)

| asset | class | p(fail by H) | risk (EUR) |
|-------|-------|--------------|------------|
| P04   | A     | 0.98         | 367 689    |
| P02   | A     | 0.98         | 250 022    |
| P16   | A     | 0.64         | 215 285    |
| P14   | A     | 0.98         | 192 678    |

A/B/C classes split the fleet 6/6/6. Full per-asset rows (incl. the
`explanation` strings) are in the results JSON.

### 4.4 Schedule (capacity 3, MILP)

5 planned interventions, none on window days, at most 2 per day; the
exact (asset, day) map is in the JSON. Assets P05..P17 with long RUL are
deliberately left unmaintained.

---

## 5. Known limitations (honest list)

1. **All inputs are assumptions.** RUL distributions and costs are
   planner inputs; absolute EUR figures do not transfer to a real plant.
2. **No RUL-error robustness claimed.** The reality check uses the same
   RUL data as the plan; a schedule is only as good as its RUL input.
   Sensitivity to RUL error is a Phase 9 research item.
3. **Single maintenance action per asset, zero maintenance duration.**
   No modelling of maintenance time, material supply or multi-day
   interventions.
4. **Linear cost matrix.** Non-linear (e.g. progressive) maintenance
   costs are the CVXPY / convex upgrade path, documented but not built.
5. **Greedy is naive by design.** It is included as the "no optimisation"
   bar, exactly as the Phase 5 rule classifier was for ML.

## 6. Files

- `optimization/criticality.py` - P(fail), risk, A/B/C classes,
  explained scores
- `optimization/scheduler.py` - MILP (HiGHS), cost matrix, greedy and
  do-nothing baselines, reality-check accounting
- `scripts/run_optimization_experiment.py` - the Phase 6 experiment
- `tests/test_optimization.py` - criticality + scheduling tests
- `experiments/results/optimization_comparison.json` - results artefact