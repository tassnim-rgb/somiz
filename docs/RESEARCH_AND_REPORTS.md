# Research and Reports (Phase 9)

Phase 9 delivers two tracked capabilities, both driven by **executed**
simulations only:

1. **Research experiments** - five bounded experiments comparing detectors,
   noise robustness, early detection, the false-alarm/false-negative tradeoff,
   and the value of optimisation under different cost structures.
2. **Automatic reports** - an HTML + PDF report (jinja2 + WeasyPrint) that is a
   pure projection of the versioned result artefacts.

Honesty rule applied throughout: every number in the report comes from a
versioned JSON experiment artefact. Nothing is fabricated; nothing is
recomputed inside the report generator.

## 1. Research experiments

Run with:

```bash
python scripts/run_research_experiments.py
```

It writes `experiments/results/research_comparison.json` (tracked) and prints
the tables. Fleet: 17 SIMULATED runs of 900 s (healthy + 5 fault modes x onset
at [100, 300, 500] s), statistical scorers only, no heavy training, runtime
about 6 s.

| Experiment | Question | Measured result (SIMULATED) |
|---|---|---|
| 6.1 Twin vs statistical vs hybrid | Does the health-index "twin" detect as well as the RMS z-score baseline? | AUC 0.966-1.000 for all three; statistical has the slight edge (0.988-1.000), twin is competitive and explains which sensors, hybrid adds nothing |
| 6.2 Noise robustness | Does detection lag degrade gracefully with sensor noise? | FAR held at ~2% (recalibrated threshold); delay stable 173-287 s up to x2 noise; at x4 the first crossing happens on a noise fluctuation (severity 0.30 vs 0.64 at x2): shorter delay there is a noisy crossing, not better detection |
| 6.3 Early detection | Is an early fault (100 s) caught with the same delay as a late one (500 s)? | With a constant progression ramp: yes, delay is broadly onset-independent per mode (bear 17-20 s, blockage 29-32 s, impeller 37-52 s, leakage 45-63 s, overheating 49-70 s) |
| 6.4 FA/FN tradeoff | Where is the operating point? | Threshold 0.8: FAR 1.79 %, missed fault samples 3.46 % (2861 fault samples) |
| 6.5 Optimisation value | Does MILP beat greedy as cost structure and capacity change? | Capacity free (2/day): greedy reaches the optimum (gap 0 %). Capacity 1/day: MILP 4.3 % to 14.3 % cheaper than greedy depending on maintenance/failure cost ratio |

Caveats that are part of the results, not bugs:

- The early-detection ramp is held constant (450 s) so that a later onset
  differs only in *when* the fault starts; the first draft that kept the ramp
  equal to `900 - onset` was discarded because it confounded onset with ramp
  steepness.
- The x4 noise "shorter delay" is interpreted as a noise-induced early
  crossing, evidenced by the severity-at-detection column.
- Uncertainties in the RUL plan (robustness of the schedule to RUL-prediction
  error) are deliberately left open; this phase reports the optimisation value
  under the simulated RUL/coût inputs, not a robustness proof.

## 2. Automatic report generation

```bash
python scripts/generate_report.py
```

Reads the four versioned artefacts
(`anomaly_comparison.json`, `diagnosis_rul_comparison.json`,
`optimization_comparison.json`, `research_comparison.json`) and renders:

- `reports/generated/somiz_report.html`
- `reports/generated/somiz_report.pdf` (A4, 4 pages, footer with page numbers)
- `reports/generated/report_manifest.json` (provenance: generated-at, page
  count, sizes, artefact list)

The PDF is produced by WeasyPrint (installed with `pip install weasyprint`;
requires pango/cairo system libraries, present on this machine and enforced by
the pytest regression test `tests/test_report_generation.py`).

The report is a projection layer: it performs no metric computation. It
re-uses measured values only (e.g. RUL interval coverage 0.9053 from Phase 5)
and rounds display values. The template lives in
`reports/templates/somiz_report.html.j2`.

`reports/generated/` is gitignored (regenerable); the artefacts and the
template are tracked.

## 3. Honest labels summary

- All data: SIMULATED physics runs (Phase 2 simulator).
- All detection / diagnosis / RUL numbers: measured on those runs.
- Heuristic diagnosis (no ML) macro-F1 0.314 is presented as the honest naive
  bar; the ML classifiers reach macro-F1 0.998-0.9995 (also on simulated data).
- The optimisation savings are optimal for the simulated RUL/cost inputs only.
- No SOMIZ deployment claim exists anywhere in this repository.