# PROJECT AUDIT — somiz (`tassnim-rgb/somiz`)

**Audit date:** 2026-09-24
**Auditor role:** industrial AI / simulation / software engineering review
**Purpose:** Phase 0 of transforming the existing SOMIZ demo into a serious
"Industrial Equipment Digital Twin & Predictive Maintenance Decision-Support
Platform". This document records what exists today, what is missing, the
proposed target architecture, and the development roadmap. **Nothing in this
document modifies the existing project:** it is an inspection deliverable.

---

## 1. Executive summary

The current repository is a **single-file, browser-only "digital shadow"
demo** written in French, modelled on the SOMIZ industrial site (Arzew,
Algeria). It renders a 3D plant floor plan (Three.js r128) with 4 ateliers
and 54 machines, each with a small live sensor panel driven by a lightweight
procedural process simulation embedded in JavaScript. It has no backend, no
database, no persisted data, and **no machine-learning, optimisation, or
decision-support capability**. It is honestly labelled as simulated
("FLUX SIMULÉ ACTIF") and its README states there is no live PLC/SCADA feed.

The demo is a competent and visually strong 3D dashboard **prototype**, but
it is not (yet) an engineering platform: the simulation is not physics-based,
results are not reproducible, and there is no evaluation, analysis,
optimisation, or persistence of any kind.

**Verdict:** preserve the 3D plant visualisation and the machine roster as a
front-end asset; build everything else as real engineering components behind
and around it.

---

## 2. Current architecture

```
Browser
  └── index.html  (single file: HTML + CSS + JS + simulation + Three.js scene)
        ├── DOM/CSS  : dark industrial theme, top bar, sidebar (4 ateliers),
        │             stat chips, event feed, inspector panel
        ├── SIM      : embedded procedural process model (see §4)
        ├── 3D       : Three.js r128 scene, orbit/zoom, raycasting, tooltips,
        │             per-status machine animation, status beacons
        └── TICKERS  : setInterval tickSensors (2 s), tickHealth (6 s),
                       tickClock (1 s), requestAnimationFrame (60 fps)
```

| Property | Value |
|---|---|
| Language | JavaScript (vanilla), single HTML file |
| Runtime | Any modern browser; no build step, no package manager |
| External deps | Three.js r128 (cdnjs CDN), IBM Plex fonts (Google Fonts) |
| Backend | **None** |
| Database | **None** |
| Tests | **None** |
| CI/CD | GitHub Pages deployment only (no test/build pipeline) |
| Branches | `main`, `gh-pages` (deployed artifact), `portfolio-polish` (merged) |
| License | MIT © BELAGHIT Tassnim Alla, 2026 |
| Local copy | `/home/nebula/projects/somiz` (audit working copy, cloned from GitHub) |

---

## 3. Current functionality

1. **3D atelier navigation** — four ateliers (DIS, DLOG, Centrale, DCA) with
   named zones, per-machine 3D geometry from 9 archetypes (tour/lathe,
   fraiseuse/mill, scie/saw, presse/press, compresseur, four/oven, perceuse/
   drill, ventilateur/vent, générique), orbit/zoom, hover tooltips, click-to-
   inspect, status beacons and emissive colour per health state.
2. **Live sensor panels** — 3 channels per machine archetype (e.g. vibration,
   temperature, RPM; or pressure, speed, load), updated every 2 s.
3. **Health engine** — a hidden scalar `_wear ∈ [0,1]` per machine; status
   (`ok → warn → danger → critical`) is derived from wear thresholds; wear
   drifts up with age/criticality, suffers rare random shocks, and is
   occasionally reset by simulated corrective maintenance.
4. **Event feed** — status transitions, maintenance actions, and sensor
   exceedance micro-events, timestamped (cap 8 entries).
5. **Machine animation** — moving parts advance at speed/roughness/glow set
   by health state (healthy smooth → critical stuttering/near-seized).
6. **Inspector panel** — health badge, criticality class (A/B/C), age, last
   /next maintenance dates, sensor readouts, intervention history.
7. **Summary chips** — per-atelier counts by health state.
8. **Hosted demo** — GitHub Pages at `https://tassnim-rgb.github.io/somiz/`.

---

## 4. Existing mathematical / simulation model

The only "model" in the project is the embedded JS process model (lines
187–254 of `index.html`). It is **procedural and illustrative**, not
physics-based:

```
value = mean(wear) × (1 + AR(1)-like noise) × (1 + rotary periodic)
```

Mechanics:

- `mean` creeps toward a status-scaled target: `target = base × SENSOR_SCALE`.
  `SENSOR_SCALE = { ok:1.0, warn:1.18, danger:1.50, critical:1.95 }`.
- Noise term: `n = 0.88·n + U(−1,1)·0.12` (loose AR(1) coloured noise).
- Periodic term: `sin(φ)` scaled by wear-induced imbalance growth.
- Wear dynamics: `w += rate·U(0,1)` with `rate = 0.0035·(1+age/30)·(criticality
  factor)`, plus 0.6%/tick chance of a +0.10–0.25 shock, minus random
  corrective maintenance when `w > 0.6`.
- Status bands: `w<0.45 ok, <0.70 warn, <0.88 danger, else critical`.
- Exceedance alarm: value > `1.25 × base × SENSOR_SCALE[status]`.

**Assessment:**

- The shape of the generative process (wear-driven drift + coloured noise +
  periodic imbalance) is a *reasonable conceptual starting point* for sensor
  synthesis, and the wear→status→symptoms chain is genuinely the right
  architecture for a health engine.
- However: there are **no differential equations, no conservation laws, no
  physics parameters** (mass, inertia, thermal capacitance, hydraulic
  resistance, efficiency maps). Units exist as labels but nothing constrains
  values to physical consistency. Constants (`SENSOR_SCALE`, wear bands,
  0.0035, 0.88, 1.25) are uncalibrated magic numbers.
- The simulation is **not reproducible** (stateless `Math.random()`, no
  seed), **not persisted**, and **not evaluable** (no ground-truth fault
  timeline, no recording, no metrics).

---

## 5. Existing data

**There is no persisted data of any kind.** Facts:

- No datasets on disk, no database, no CSV/Parquet, no history storage.
- Every page load regenerates sensors/wear from `Math.random()`; nothing is
  correlated across reloads or across machines beyond the instantiated
  archetype/status.
- The machine roster (IDs, names, ages, criticality A/B/C, maintenance
  dates, intervention history) is **illustrative placeholder data**, as the
  README explicitly states. History entries use 2024 dates while the project
  is licensed 2026 — cosmetic, but worth cleaning to avoid inconsistency.
- No error/outlier/missing-data injection exists.

**Validation discrepancy found:** the README claims *"4 ateliers, 69
machines"*; the actual roster contains **54 machines** (DIS 24, DLOG 6,
Centrale 17, DCA 6). The README counts must be corrected during the build
(no fabrication — state the verified number).

---

## 6. Existing ML / analytics assets

**None.** No anomaly detection, fault diagnosis, RUL estimation, health
index computation, forecasting, or trained models of any kind. The health
"score" is a single hidden wear scalar with hand-picked thresholds — there is
no evaluable model surface to compare.

---

## 7. Existing visualizations / GUI components

| Component | Technology | Quality | Reuse? |
|---|---|---|---|
| 3D atelier floor plan + machines | Three.js r128 | Strong, distinctive | ✅ Preserve as "Plant 3D view" |
| Status beacons / emissive health colouring | Three.js | Good | ✅ Keep in rebuilt UI |
| Machine archetype geometry builders | Three.js | Good (9 archetypes) | ✅ Refactor into a module |
| Inspector panel (sensors, history) | DOM/CSS | Basic, no charts | 🔁 Rebuild (charts needed) |
| Event feed | DOM/CSS | Basic | 🔁 Rebuild (persisted + richer) |
| Stat chips | DOM/CSS | Basic | 🔁 Rebuild (driven by backend) |
| No time-series charts, no maps, no tables | — | Missing | ➕ Add per spec |
| No cost/risk/schedule visualisation | — | Missing | ➕ Add per spec |

---

## 8. Original SOMIZ design intent

The demo was designed as a browsable "digital shadow": a faithful-looking
site model (SOMIZ, Arzew — real site name used with permission intent; 4
ateliers, machine archetypes, French UI) used to communicate what a smart
maintenance dashboard *would* look like. The README states explicitly:

- Data is **simulated**; there is no live sensor feed (no PLC/SCADA/TIWEST).
- Plant layout, equipment names and maintenance records are **illustrative
  placeholders**, not exported plant data.
- The code is deliberately structured so the simulation can be swapped for a
  real telemetry bridge (`genSensors` / `tickSensors` / `tickHealth` are the
  only writers of sensor values / status).

**Design consequence for the transformation:** the replacement system must
preserve this honesty posture. It will be a **generic, configurable digital
twin research platform** whose asset parameters can be instantiated later
with real company data. It must **never** claim deployment at SOMIZ, and all
generated data must be labelled as simulation.

---

## 9. Current limitations (engineered, not cosmetic)

1. **No physics** — no ODEs, no state vector, no parameters; sensors do not
   satisfy conservation laws or energy balances.
2. **No reproducibility** — unseeded RNG; results differ every reload.
3. **No persistence** — no database, no recording, no export.
4. **No backend/API** — everything client-side; no external integration
   surface (no telemetry bridge possible from the browser).
5. **No ML pipeline** — no anomaly detection, diagnosis, RUL, uncertainty,
   or explainability; no training/evaluation.
6. **No optimisation** — no cost/risk model, no scheduling, no resource
   constraints, no criticality computation (A/B/C is static decorative data).
7. **No data-pipeline hygiene** — no missing data, outliers, sensor faults,
   train/test discipline; no feature engineering.
8. **Scale illusion** — `tickSensors`/`tickHealth` only iterate over the
   *current* atelier (24 of 54 machines are actually simulated at any time),
   and the event feed caps at 8 entries.
9. **No tests, no CI** (Pages deploy only), no linting, no type checking.
10. **No documentation beyond README** — no architecture, no model maths,
    no API, no deployment, no limitations docs.
11. **No security consideration** — nothing to secure today, but the target
    adds an API/database that must be handled correctly (validation, keys in
    env, no secrets committed).
12. **Factual slips** — README says *69 machines* (54 actual); dates are
    2024 while license is 2026. (README machine count fixed in Phase 10:
    now states 54 exactly, matching `index.html`; dates remain illustrative
    SIMULATED data.)

---

## 10. Missing components vs. the target vision

| Target capability (vision) | Status today |
|---|---|
| Configurable industrial asset model (physics params, failure modes, states) | ❌ None |
| Mathematical digital twin (`dx/dt = f(x,u,θ)`, `y = h(x,u,θ)+ε`) | ❌ None (procedural JS only) |
| Failure-mode simulation (onset/severity/progression/ground truth) | ◐ Partial illusion (random shocks) |
| Reproducible synthetic sensor data engine (CSV/Parquet) | ❌ None |
| Data pipeline (validation, imputation, features, chronological splits) | ❌ None |
| Anomaly detection (statistical, Isolation Forest, autoencoder, temporal) | ❌ None |
| Fault diagnosis (classifier + probabilities + severity) | ❌ None |
| RUL / degradation estimation | ❌ None (wear scalar only) |
| Health index (computable, explained, 0–100) | ◐ Wear scalar, unexplained thresholds |
| Maintenance decision engine (cost/risk optimisation) | ❌ None |
| Maintenance scheduling (multi-asset, resources) | ❌ None |
| Asset criticality model (explained scoring) | ◐ Static A/B/C labels only |
| Digital-twin dashboard (overview/asset/map/sim/planner/analytics) | ◐ Visual shell only |
| Backend API (FastAPI) | ❌ None |
| SQLite database (assets, measurements, faults, maintenance, plans…) | ❌ None |
| Experiment framework + model comparison (reproducible) | ❌ None |
| Physics-vs-ML-vs-hybrid study | ❌ None |
| Uncertainty / confidence intervals | ❌ None |
| Explainability (SHAP, sensor attribution) | ❌ None |
| Automatic report generation (HTML/PDF) | ❌ None |
| Technical documentation set + docs/ diagrams | ◐ README only |
| Automated tests (model, sim, data, API, optimisation, ML, edge cases) | ❌ None |
| Security hygiene (.env, input validation) | ❌ N/A (no backend) |
| Containerised deployment (`docker compose up`) | ❌ None |
| Professional industrial UI (charts, tables, asset cards, responsive) | ◐ 3D strong, analytics absent |
| Research component (twin→anomaly, noise→maintenance, FA/FN tradeoff…) | ❌ None |
| CV material (CV_DESCRIPTION.md, INTERVIEW_PREPARATION.md) | ❌ None |

---

## 11. Proposed target architecture

### 11.1 Top-level design philosophy

- **A single scientific chain** (mandatory, from the vision):

```
PHYSICAL SYSTEM → MATHEMATICAL MODEL → DIGITAL TWIN → SENSOR DATA
→ STATE ESTIMATION → HEALTH MONITORING → ANOMALY DETECTION
→ FAULT DIAGNOSIS → DEGRADATION/RUL → MAINTENANCE OPTIMIZATION
→ DECISION SUPPORT → WEB DASHBOARD
```

- **Honesty first:** everything generated is simulation; the asset is a
  configurable generic industrial machine (backbone: a rotating machine
  family — motor-driven pump/compressor — with plug-in failure modes); no
  SOMIZ-specific or fabricated plant data enters the system; every artifact
  is labelled (REAL / SIMULATED / MODEL ASSUMPTION / EXPERIMENTAL RESULT /
  HYPOTHETICAL EXAMPLE, never mixed).
- **Reuse over rewrite:** the Three.js plant view becomes the "Plant" view of
  the new dashboard; the 9 archetype builders become a reusable module; the
  machine roster becomes seeded initial data (corrected counts).
- **Simplicity with substance:** architecture shaped to be *runnable and
  testable by one engineer*, deferring "résumé keywords" unless they serve a
  real function.

### 11.2 Technology choices (justified)

| Layer | Choice | Why (and why not something else) |
|---|---|---|
| Backend | **FastAPI** (Python 3.11+) | Async, typed, auto OpenAPI; natural fit with the scientific stack; Uvicorn. |
| Digital twin / simulation | **NumPy + SciPy** (`scipy.integrate`) | Real ODE solver, vectorised batch runs; the core mathematical engine. |
| ML | **PyTorch** (autoencoder, temporal nets) + **scikit-learn** (statistical, Isolation Forest, RF, XGBoost optional) | Autoencoder/RUL nets need autodiff; sklearn for tabular baselines. |
| Optimisation | **SciPy `optimize` + CVXPY** | Convex cost/risk formulation (CVXPY) for decision engine; MILP-style schedule via scipy/OR-Tools only if a genuine need appears (keep dependency surface minimal initially). |
| Database | **SQLite via SQLAlchemy** | Zero-ops prototype DB; schema abstracted so PostgreSQL is a swap later. |
| Frontend | **React + Vite + TypeScript**, Plotly (or ECharts) + re-used Three.js for the plant view | The spec asks for a professional dashboard; Vite is fast, TS keeps a growing codebase sane. Vanilla JS was considered — rejected because the dashboard has 6 pages of stateful charts. |
| Reports | **WeasyPrint or ReportLab (HTML→PDF)** | Deterministic technical reports incl. PDF. |
| Testing | **pytest + pytest-asyncio + httpx** | Standard, suffices for model/sim/API/opt. |
| Containerisation | **Docker** (`docker-compose.yml`, dev + prod profiles) | `docker compose up` per spec. |
| CI | GitHub Actions: lint+tests+export-check on push to `main` | Builds on the existing Pages flow. |

### 11.3 Repository structure

```
somiz/
├── backend/            # FastAPI app (app/, routers/, schemas/, deps/)
├── simulation/         # Physical asset models + ODE integration (pure, backend-agnostic)
├── digital_twin/       # State estimation (KF/PF), health index, residual monitor
├── data/               # generated datasets (gitignored), schema, seed configs
├── models/             # trained artifacts (gitignored)
├── ml/                 # anomaly detection, diagnosis, RUL, uncertainty, explainability
├── optimization/       # decision engine (cost/risk), scheduling, criticality
├── experiments/        # reproducible experiment runner + results registry
├── tests/              # pytest suites (model, sim, data, ML, API, opt, edge cases)
├── docs/               # architecture diagrams (Mermaid), design notes
├── reports/            # generated HTML/PDF reports (gitignored outputs)
├── notebooks/          # exploration notebooks (labelled)
├── scripts/            # CLI: generate-data, train, evaluate, report, demo
├── frontend/           # Vite+React+TS dashboard (Vite app)
├── webui/              # (kept) original single-file index.html as legacy reference? → moved under frontend/legacy or docs/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── README.md
├── ARCHITECTURE.md / MATHEMATICAL_MODEL.md / DIGITAL_TWIN.md /
│   DATA_GENERATION.md / ML_PIPELINE.md / OPTIMIZATION.md / API.md /
│   DEPLOYMENT.md / LIMITATIONS.md / CV_DESCRIPTION.md / INTERVIEW_PREPARATION.md
├── PROJECT_AUDIT.md   # this document
└── LICENSE (MIT, kept)
```

> The original `index.html` is **preserved** (moved rather than deleted) so
> the legacy demo remains runnable and diffable.

### 11.4 Core data / object flow

```mermaid
flowchart LR
    subgraph SIM["Simulation core (Python)"]
        A[Asset config<br/>physics params, failure modes] --> B[ODE integrator<br/>dx/dt=f(x,u,theta)]
        B --> C[Sensor model<br/>y=h(x,u,theta)+eps]
        C --> D[(SQLite<br/>measurements, faults)]
    end
    subgraph ML["ML pipeline"]
        E[Preprocessing<br/>impute, norm, features, chrono split] --> F[Anomaly detection]
        F --> G[Fault diagnosis]
        F --> H[RUL / degradation]
        G --> I[Explainability<br/>SHAP / attribution]
    end
    D --> E
    subgraph OPT["Decision layer"]
        J[Health index] --> K[Cost-risk engine<br/>failure prob, downtime, cost]
        K --> L[Maintenance schedule<br/>resources, windows, criticality]
    end
    H --> J
    F --> J
    subgraph API["FastAPI"]
        M[REST endpoints] --> N[OpenAPI / docs]
    end
    L --> M
    I --> M
    D --> M
    subgraph UI["Frontend (Vite+React)"]
        O[Overview] --> P[Asset list/map]
        P --> Q[Asset detail]
        Q --> R[Simulation lab]
        Q --> S[Maintenance planner]
        Q --> T[Analytics]
        P --> U[3D Plant view<br/>legacy Three.js module]
    end
    N --> UI
```

### 11.5 Proposed database schema (SQLite, PostgreSQL-ready)

```
assets(id, asset_type, name, description, params_json, criticality_json,
       created_at, retired_at)
sensors(id, asset_id FK, tag, name, unit, kind, meta_json)
measurements(id, asset_id FK, sensor_id FK, ts, value, quality_flag)
faults(id, asset_id FK, fault_type, onset_ts, severity, progression_params,
       ground_truth_state, notes)
anomalies(id, asset_id FK, ts, score, threshold, is_detected, true_onset_ts,
          detection_delay, false_alarm_flag)
diagnoses(id, asset_id FK, ts, fault_type, probability, severity_estimate,
          affected_signals_json, method, model_version)
predictions(id, asset_id FK, ts, health_index, rul_estimate, rul_lower,
            rul_upper, confidence, model_version)
maintenance_events(id, asset_id FK, scheduled_at, performed_at, action_type,
                   cost, duration_h, resources_json, outcome)
maintenance_plans(id, generated_at, horizon_days, plan_json, objective_value,
                  solver, constraints_json)
experiments(id, name, config_json, metrics_json, artifacts_json, created_at)
```

---

## 12. Proposed development roadmap (13 steps)

Each phase ends with: **tests run → results inspected → changes documented**.
Nothing is reported as measured unless it was actually measured.

| # | Phase | Deliverables | Gate |
|---|---|---|---|
| 1 | Audit | `PROJECT_AUDIT.md` + architecture sign-off (this doc) | ✅ user approval |
| 2 | Core asset + simulation | `simulation/` Python package: rotating-machine ODE family (states: rotor speed, temperature, flow/pressure, efficiency, wear), startup/shutdown/load/degradation regimes, failure-mode catalog, configurable noise/drift/missing/outlier/sensor-failure | unit tests, physical sanity checks |
| 3 | Data engine + pipeline | seeder → SQLite + CSV/Parquet export; preprocessing (validation, imputation, normalisation, rolling/frequency features, chronological splits, leakage guards) | data-quality tests |
| 4 | Health + anomaly | health index (explained formula), statistical baseline / Isolation Forest / autoencoder / temporal; metrics: P/R/F1, false-alarm rate, detection delay | comparison table |
| 5 | Diagnosis + RUL | fault classifier (RF/XGBoost/NN vs baseline), severity; RUL (baseline regression vs temporal net); uncertainty (quantiles/CIs); SHAP attribution | comparison table |
| 6 | Optimisation | cost/risk decision engine (CVXPY), maintenance scheduling (resources, windows, criticality), criticality model | feasibility + constraint tests |
| 7 | Backend API | FastAPI endpoints per spec, SQLite via SQLAlchemy, validation, OpenAPI docs | API tests |
| 8 | Dashboard | Vite+React+TS: Overview / Asset map / Asset detail / Simulation lab / Maintenance planner / Analytics + rebuilt 3D plant view | e2e against backend |
| 9 | Reports + research | auto HTML/PDF reports; research experiments (twin-vs-ML-vs-hybrid, noise robustness, early detection, FA/FN tradeoff, uncertainty, optimisation value) | executed experiments only |
| 10 | Docs | README + 9 technical docs + `docs/` Mermaid diagrams | doc review |
| 11 | Tests + security | edge-case suite, `.env` handling, input validation, secrets scan | green CI |
| 12 | Deployment | Dockerfile + compose, `.env.example`, Pages/self-host instructions, free-tier note | `docker compose up` verified |
| 13 | CV material | `CV_DESCRIPTION.md`, `INTERVIEW_PREPARATION.md` | final summary |

---

## 13. Decisions required from the owner (Phase 1 gate)

Before implementation starts, the following scope choices must be confirmed:

1. **Location** — build in `/home/nebula/projects/somiz` (created above) as a
   new branch (`digital-twin-platform`) off `main`; merge only on approval.
2. **Flagship asset** — start with a configurable **rotating machine family**
   (motor + centrifugal pump set / compressor), the most classic
   PdM use-case; other archetypes become configuration, not new code.
3. **Frontend stack** — React+Vite+TS+Plotly (recommended) vs. lighter
   vanilla/htmx dashboard; the 3D plant view is reused either way.
4. **Optimisation stack** — CVXPY + SciPy (recommended) vs. OR-Tools.
5. **Language of the UI** — keep French labels (site context) with English
   technical core, or full English; affects all dashboard copy.
6. **README correction** — 54 machines (verified) replaces the stated 69.
7. **Commit discipline** — audit + scaffold commits on `digital-twin-platform`;
   `main` untouched until the platform is functional and reviewed.

---

*End of audit. No source files of the existing project were modified.*