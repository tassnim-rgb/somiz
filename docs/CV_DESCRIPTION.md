# CV description — SOMIZ digital-twin platform (Phase 13)

> **Honesty rule for this document.** Every number below traces to a
> versioned result artifact under `experiments/results/` or `docs/` and is
> explicitly **SIMULATED / MODEL ASSUMPTION**. Nothing in this project
> describes a real plant. Personal fields that are not verified are marked
> `TO CONFIRM` and must be filled by you, never invented.
>
> Verified identity facts (real): **Tassnim Belaghit**,
> tassnim.belaghit@nhsm.edu.dz, GitHub `tassnim-rgb`.

## 1. Project portfolio entry (ready to paste)

> Built a complete, end-to-end industrial digital-twin platform — from
> physics simulation through machine learning and decision optimisation to a
> live web dashboard and deployment — as a 13-phase engineering project
> (`tassnim-rgb/somiz`, MIT). The system simulates a fleet of
> motor-driven centrifugal pumps; every value is explicitly labelled
> SIMULATED and every reported metric is traceable to a versioned result
> artifact, so nothing is claimed beyond what was measured.

**What I built (by area):**

- **Physics twin** — RK4 time-domain simulation of a rotating machine
  (mechanical, thermal, hydraulic and electrical coupled equations),
  degradable faults (bearing, overheating, leakage, impeller, blockage)
  with progressive severity, sensor telemetry with noise/dropouts/outliers,
  and a reproducible seed. `simulation/`, `docs/MATHEMATICAL_MODEL.md`.
- **Data pipeline** — validation, linear/ffill imputation, fit-on-train-only
  normalisation, rolling/rate-of-change/spectral features, chronological
  splits with anti-leakage guarantees and a documented transform log.
  `pipeline/`.
- **Machine learning** — four unsupervised anomaly detectors (statistical
  baseline, isolation forest, two PyTorch autoencoders), an explainable
  health index (0-100 with WARMUP/NO_READING honesty semantics), fault
  diagnosis, remaining-useful-life (RUL) with uncertainty intervals, and
  SHAP-style explainability. `ml/`, `digital_twin/`.
- **Decision optimisation** — MILP maintenance scheduling (scipy HiGHS:
  crew capacity, no-maintenance days, preventive-vs-reactive cost windows),
  risk/criticality model, greedy and do-nothing baselines.
  `optimization/`.
- **API + dashboard** — FastAPI REST with typed Pydantic validation and
  OpenAPI docs; React + Vite + TypeScript + Plotly dashboard (7 pages,
  French UI copy, English technical core). `backend/`, `frontend/`.
- **Reports** — HTML/PDF report generator from tracked result artifacts
  (WeasyPrint). `reports/`.
- **Testing & security** — 209 automated tests (simulation, physics,
  sensors, health index, anomaly, diagnosis, RUL, optimisation, pipeline,
  API, edge cases, .env handling); GitHub Actions CI (pytest + secrets
  scan); reproducible secret scanner; validated inputs with no-secrets
  discipline. `tests/`, `.github/workflows/ci.yml`, `docs/SECURITY.md`.
- **Deployment** — live on Vercel (Services: FastAPI + Vite SPA, SQLite
  seed at build time), with a documented Docker self-host persistence path.
  Live demo: <https://somiz.vercel.app> (SIMULATED).

**Measured results** (all SIMULATED, all traceable):

| Result | Value | Artifact |
| --- | --- | --- |
| Anomaly detection, statistical baseline | AUC 0.9969, F1 0.979, FAR 2.5 %, delay 31 s at FAR 2 % | `experiments/results/anomaly_comparison.json` |
| Anomaly detection, isolation forest | AUC 0.8615 | same |
| Health-index twin vs detectors, 5 failure modes | AUC 0.966–0.996 (twin), 0.988–1.0 (statistical); delays 20–79 s; FAR ≈ 2 % | `experiments/results/research_comparison.json` |
| Diagnosis, honest rule-based bar | accuracy 0.41, macro-F1 0.314 (explicit per-class failure analysis) | `experiments/results/diagnosis_rul_comparison.json` |
| Diagnosis, supervised RF (SIMULATED in-fleet benchmark) | accuracy 0.9994, macro-F1 0.9995 | same |
| RUL, GBM (pooled, n = 108 005 test samples) | MAE 273 s (4.6 min), RMSE 655 s | same |
| RUL, quantile GBM uncertainty | p10–p90 interval coverage 90.5 % | same |
| Maintenance scheduling, MILP vs greedy (18 assets, 14 days, capacity 2) | MILP 211 127 EUR vs greedy 589 332 EUR (~64 % lower expected cost) | `experiments/results/optimization_comparison.json` |
| Test suite + CI | 209 passing; GitHub Actions green; secrets scan clean (108 tracked files) | `tests/`, CI run |
| Fleet scale (legacy refactor) | 54 machines, 4 ateliers | `frontend/index.html` legacy, `PROJECT_AUDIT.md` |

## 2. Ready-to-use achievement bullets

Short, metric-first bullets (English, safe for a CV):

- Built a full-stack industrial digital-twin platform end to end across 13
  disciplined phases: physics simulation, data pipeline, machine learning,
  optimisation, REST API, web dashboard, reports and deployment.
- Reached AUC 0.997 with a statistical baseline anomaly detector and
  2%-FAR detection in ~31 s on simulated telemetry, with honest false-alarm
  reporting.
- Reduced expected maintenance cost by ~64 % versus a greedy baseline with
  an exact MILP scheduler (HiGHS) on an 18-asset simulated fleet.
- Implemented an explainable health index and RUL model with calibrated
  p10-p90 intervals (90.5 % coverage) instead of point estimates.
- Shipped a live, documented deployment (Vercel: FastAPI + React), 209
  automated tests, edge-case suite, and a repository-wide secrets scan
  wired into CI.
- Maintained a strict honesty discipline: every number traceable to a
  versioned artifact, everything SIMULATED, no fabricated claims.

## 3. Tech stack (with evidence)

Python (NumPy, SciPy, Pandas, scikit-learn, PyTorch optional),
FastAPI, SQLAlchemy, SQLite (+ PostgreSQL-ready schema), React, Vite,
TypeScript, Plotly, GitHub Actions, Vercel, WeasyPrint, Git.

## 4. Personal fields — TO CONFIRM (do not leave blank in a real CV)

| Field | Value |
| --- | --- |
| Full name | Tassnim Belaghit (verified) |
| Email | tassnim.belaghit@nhsm.edu.dz (verified) |
| GitHub | tassnim-rgb (verified) |
| Phone | TO CONFIRM |
| Location | TO CONFIRM |
| Education / degree | TO CONFIRM |
| Languages | TO CONFIRM |
| Work experience | TO CONFIRM |
| LinkedIn / portfolio URL | TO CONFIRM |

## 5. How to present it honestly

- Always say the data is **simulated**; never claim a deployment on a real
  plant, real telemetry, or real savings.
- Quote metrics together with their artifact (`experiments/results/…`) and
  the fleet/scenario context (e.g. "on an 18-asset SIMULATED fleet").
- When asked "does it work on real data?", the honest answer is: the
  pipeline is built to ingest real telemetry (OPC-UA placeholder in
  `.env.example`), but no real plant data has ever been used.