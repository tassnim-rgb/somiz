# SOMIZ Dashboard (Phase 8)

The dashboard is the **thin display layer** of the SIMULATED digital-twin
platform. It holds no data of its own: every value is fetched from the
Phase 7 FastAPI backend, which serves a SIMULATED SQLite fleet. Nothing
in this UI describes a real plant.

## Stack

- **Vite + React + TypeScript** (strict mode, `tsc --noEmit` in the build)
- **Plotly** (`react-plotly.js` + `plotly.js-dist-min`) for time series,
  bars and the maintenance Gantt
- **Three.js** for the rebuilt "Vue 3D du site" (scene is illustrative:
  boxes colored by the health index, emissive beacons on degraded assets,
  OrbitControls, hover tooltip)
- **React Router** for navigation; dev proxy `/api` and `/health` to the
  backend on `127.0.0.1:8000` (CORS is also open on the backend for the
  built app)

## Views

| View | Content |
|---|---|
| Vue d'ensemble | stat chips, health-stage distribution, latest MILP plan |
| Plan des machines | asset cards with health badge, criticality class, RUL, P(fail), risk |
| Détail de l'actif | sensor time series with picker, health index + severity chart, diagnostics table, planned events |
| Maintenance | MILP plan card, day-by-day bar chart, events table |
| Analyse | fault counting, anomalies by asset, health index per asset, experiment catalogue |
| Laboratoire de simulation | run a SIMULATED physics run on demand (`POST /api/simulate`): scenario, seed, duration |
| Vue 3D du site | illustrative Three.js plant view, hover to inspect |

## Honesty rules respected in the UI

- Persistent "Données SIMULÉES" badge and per-page provenance notes.
- Health index is never fabricated: WARMUP / NO_READING samples render as
  "Pas de lecture".
- Diagnoses from the seed are labeled `ground_truth_seed`; the Phase 5 ML
  models are the documented replacement.
- The maintenance plan is presented as the MILP result on SIMULATED
  planning inputs, not as a real schedule.

## Run

```bash
# backend (seeded DB)
python scripts/seed_database.py --reset
uvicorn backend.main:app --port 8000

# dashboard (dev, proxies /api to :8000)
cd frontend && npm install && npm run dev      # http://localhost:5173

# production build
cd frontend && npm run build                   # npm run preview to serve dist
```

## Build

`frontend/package.json` scripts: `dev`, `build` (type-check + `vite
build`), `preview`. `node_modules/` and `dist/` are gitignored. The bundle
is ~1.6 MB gzip (Plotly + Three dominate); chunk-size warnings are
accepted for this demo display layer.

## Verified

- `npm run build`: TypeScript strict check passes, production build OK.
- E2E smoke against the live backend through the vite dev proxy: app HTML,
  `/api/assets` (4 assets), `/api/simulate` for `leakage` (severity
  reaches 0.8, WARMUP samples null) and `healthy` (severity 0, no faults).
- Backend suite including `/api/simulate`: 19 API tests green.