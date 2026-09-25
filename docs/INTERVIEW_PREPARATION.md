# Interview preparation — SOMIZ digital-twin platform (Phase 13)

> Written answer to every question below is grounded in the repository
> (traceable numbers are given inline). Keep the key-numbers table at the
> end close at hand. Rule: never over-claim — the project is SIMULATED and
> that is a feature of the answer, not a flaw to hide.

## A. Tell me about the project (90-second pitch)

"I designed and built a complete industrial digital-twin platform over 13
phases: a physics-based simulation of a centrifugal-pump fleet, a data
pipeline with anti-leakage guarantees, unsupervised anomaly detection, an
explainable health index, fault diagnosis, remaining-useful-life with
uncertainty intervals, an exact MILP maintenance scheduler, a FastAPI
backend, a React dashboard, a report generator, and a live deployment on
Vercel — 209 automated tests, GitHub Actions CI, and a secrets scan.
Everything is explicitly SIMULATED and every metric is traceable to a
versioned result artifact. Live demo: https://somiz.vercel.app."

## B. Architecture questions

**Q: Walk me through the architecture.**
A: One data chain: simulation (`simulation/`, RK4 physics twin) → pipeline
(`pipeline/`, validation/imputation/normalisation/features with
chronological splits) → ML (`ml/`, `digital_twin/`: anomaly detectors,
health index, diagnosis, RUL) → optimisation (`optimization/`, MILP
scheduler + criticality) → FastAPI (`backend/`) → React dashboard
(`frontend/`). Every layer has its own test module; docs/ has one page per
layer. See `docs/ARCHITECTURE.md`.

**Q: Why FastAPI?** A: Typed Pydantic validation, automatic OpenAPI docs,
async-ready, first-class TestClient, and a slim deployable bundle. It
replaced no system — the backend is built from scratch.

**Q: Why SQLite, and why 'PostgreSQL-ready'?** A: Zero-ops for a demo and a
build-time snapshot on Vercel; the ORM schema (backend/models.py) uses only
SQLAlchemy-2 typed, engine-neutral constructs (JSON columns, no SQLite
extensions), so the same models work on PostgreSQL.

**Q: Why a Vite/React/Plotly SPA instead of the legacy single-file page?**
A: The legacy `index.html` (54 machines, 4 ateliers) is preserved and kept
runnable; the SPA adds real state, 7 typed pages (overview, assets, detail,
simulation lab, maintenance, analytics, 3D plant), and Python does all the
intelligence — the dashboard is a thin display layer.

## C. ML and validation questions

**Q: How do you make sure your ML isn't cheating (data leakage)?**
A: Three mechanisms, all tested: (1) preprocessing normalisation fits on the
train slice only (`test_scaler_fit_on_train_only_…`); (2) rolling features
use `shift=1` so row t never sees future rows (`test_leakage_guard_order_preserved`);
(3) detectors fit on healthy data only — fully unsupervised for anomaly
detection.

**Q: Your diagnosis macro-F1 is only 0.314. Why quote it?**
A: Because it is the honest, rule-based baseline and the point of the
project is not to inflate numbers. A supervised random forest reaches
macro-F1 0.9995 on the same simulated fleet, but that is an in-fleet
benchmark on SIMULATED data — the honest framing is what differentiates
this project. The per-class table shows exactly where the rule-based
approach fails (leakage/impeller/blockage: F1 = 0), which is what a
scientist should be able to articulate.

**Q: Detection delay vs false alarms — how do you handle the trade-off?**
A: Every detector is evaluated at matched false-alarm rates (FAR 2 %);
e.g. statistical baseline: 31 s delay at FAR 2 %, 0 s at its best-F1
threshold (anomaly_comparison.json). The research comparison adds the
health-index twin per failure mode (delays 20–79 s). I report both axes,
never just AUC.

**Q: How do you model uncertainty?** A: Quantile-gradient-boosting RUL
gives p10/p90 intervals with 90.5 % measured coverage and mean width
3 388 s, rather than a single point estimate; the maintenance scheduler
takes p50 RUL as planning input and the plan's robustness to RUL error is
explicitly listed as Phase 9 research, not claimed.

## D. Optimisation questions

**Q: Explain your MILP scheduling problem.**
A: x[i,d] = maintain asset i on day d; one action per asset, daily crew
capacity, no-maintenance days (e.g. weekends), preventive cost inside a
safe window vs reactive cost + failure cost outside it; HiGHS via
scipy.optimize.milp. On an 18-asset SIMULATED fleet, MILP 211 127 EUR vs
greedy 589 332 EUR (~64 % lower), 5 planned preventive, 0 failures.
Assumptions are listed in optimization_comparison.json (macro_assumptions).

**Q: What would you change for a bigger problem?** A: CVXPY is documented
as the upgrade path for convex variants and/or OR-Tools for very large
integer problems; the current formulation is intentionally small and exact.

## E. Honesty and scope questions

**Q: Is this connected to a real plant?** A: No. 100 % SIMULATED. OPC-UA /
telemetry endpoints exist as placeholders in `.env.example`; the pipeline
is built to ingest real data but no real data has ever been used and I say
so explicitly in every interface.

**Q: What are the documented limitations?** A: Real plant data (none);
GPU training untested (CUDA parameter present but unverified); serverless
SQLite is read-only at runtime; diagnosis heuristic baseline is weak by
design (F1 0.314); schedule robustness to RUL error is open research. See
`docs/DEPLOYMENT.md`, `docs/SECURITY.md`, `PROJECT_AUDIT.md` findings.

## F. Security and engineering-practice questions

**Q: How do you keep secrets out of the repo?** A: `.env` gitignored with a
documented `.env.example`; `backend/env.py` loads it with strict precedence
(real env vars always win); `scripts/scan_secrets.py` scans all 108 tracked
files in CI and fails the build on any match; a leaked Vercel token was
detected via scanning discipline and revoked.

**Q: Give an example of a bug you found through testing.** A: A payload
containing the JSON literal `NaN` was correctly rejected by Pydantic but
crashed the error-response renderer (JSON cannot serialise `nan`). I added
a `RequestValidationError` handler that sanitises non-finite floats so the
API always answers a clean 422 — now covered by a regression test.

**Q: What is the honest boundary of the deployed demo?** A: The demo API
is unauthenticated with CORS `*`, no rate limiting; `POST /api/simulate` is
pure compute; writes do not persist on Vercel Functions. This is documented
and deliberate for a demo — never for real data (docs/SECURITY.md).

## G. Deployment questions

**Q: Why Vercel and what did you learn?** A: One platform for the FastAPI
service + Vite SPA with top-level rewrites. Learned: keep the serverless
bundle under 225 MB by making torch optional and isolating seed-time
dependencies; the SQLite seed must be deterministic and reproducible; the
deploy environment needed an IPv4-first workaround on this machine
(`docs/DEPLOYMENT.md`).

**Q: What about persistence?** A: On Vercel Functions the DB is a read-only
build-time snapshot; `POST /api/assets` writes do not persist there. The
documented alternative is Docker self-host with a mounted volume — the
deployment doc gives the exact path (not built, only documented).

## H. Direction questions

**Q: What would you do next?** A: (1) Ingest real telemetry and build the
supervised layers on field data; (2) train the windowed autoencoder on GPU
(CUDA hook exists, untested); (3) Docker self-host for persistence;
(4) auth + rate limiting before any real data; (5) research on schedule
robustness to RUL error; (6) LLM-assisted maintenance notes (Phase 9
already evaluates report generation with an optional LLM).

## I. Key numbers table (traceable)

| Metric | Value | Where |
| --- | --- | --- |
| Tests | 209 passing, CI green | tests/, GitHub Actions |
| Stats baseline anomaly | AUC 0.9969, F1 0.979, FAR 2.5 % | anomaly_comparison.json |
| Delay at FAR 2 % | 31 s | anomaly_comparison.json |
| Twin AUC over 5 modes | 0.966–0.996 | research_comparison.json |
| Heuristic diagnosis | macro-F1 0.314 (honest bar) | diagnosis_rul_comparison.json |
| RF diagnosis (SIMULATED) | macro-F1 0.9995 | same |
| RUL GBM | MAE 273 s, RMSE 655 s | same |
| RUL interval coverage | 90.5 % (p10–p90) | same |
| MILP vs greedy (18 assets) | 211 127 vs 589 332 EUR (~64 % lower) | optimization_comparison.json |
| Legacy scale | 54 machines, 4 ateliers | PROJECT_AUDIT.md |
| Live demo | https://somiz.vercel.app (SIMULATED) | README.md |

## J. Questions to ask the interviewer

- What data will the twin consume — real telemetry, historians, or both?
- Centralised vs edge inference for the anomaly detectors?
- How is maintenance currently planned (spreadsheets/CMMS), and what
  constraints should the scheduler respect (crew, contracts, lead times)?
- Is there an existing MLOps/CI culture, or would this be the first?
- What does "success" look like for the first production deployment?