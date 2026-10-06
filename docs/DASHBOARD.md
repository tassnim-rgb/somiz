# SOMIZ Dashboard (Phase 8)

The dashboard is the **thin display layer** of the SIMULATED digital-twin
platform. It holds no data of its own: every value is fetched from the
Phase 7 FastAPI backend, which serves a SIMULATED SQLite fleet. Nothing
in this UI describes a real plant.

## Stack

- **Vite + React + TypeScript** (strict mode, `tsc --noEmit` in the build)
- **Plotly** (`react-plotly.js` + `plotly.js-dist-min`) for time series,
  bars and the maintenance Gantt
- **Three.js** for the plan-derived "Vue 3D du site": the four ateliers
  rebuilt from the P-01 scans (98 machines / 34 zones, OCR positions),
  zone pads + projected HTML zone labels, hover/click raycasting, machines
  animated per simulated health state, OrbitControls
- **React Router** for navigation; dev proxy `/api` and `/health` to the
  backend on `127.0.0.1:8000` (CORS is also open on the backend for the
  built app)

## Views

| View | Content |
|---|---|
| Vue d'ensemble | stat chips, health-stage distribution, latest MILP plan |
| Plan des machines | 2D SVG plan of the selected atelier (zones, plan title, machines colored by simulated state; hover for name, click for the equipment panel) + instrumented API asset cards |
| Détail de l'actif | sensor time series with picker, health index + severity chart, diagnostics table, planned events |
| Maintenance | MILP plan card, day-by-day bar chart, events table |
| Analyse | fault counting, anomalies by asset, health index per asset, experiment catalogue |
| Laboratoire de simulation | run a SIMULATED physics run on demand (`POST /api/simulate`): scenario, seed, duration |
| Vue 3D du site | plan-derived Three.js plant (atelier switcher, zone labels, hover tooltip, click → equipment panel) |

Both plan views share the generated data module
`frontend/src/data/ateliers.ts` (regenerate with
`node tools/plan_layout/make_ts.js`, see `tools/plan_layout/README.md`).

## Honesty rules respected in the UI

- Persistent "Données SIMULÉES" badge and per-page provenance notes.
- Plan-derived views: positions and surfaces are OCR readings of the
  scanned plans P-01 ind. 01 and are labelled **approximate** everywhere
  (topbar chip `PLANS P-01 · IND. 01`, sidebar source note, plan grid
  label, panel footnote); machine states, ages and histories stay
  **SIMULATED** — no SOMIZ maintenance data is shown or invented.
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
- Puppeteer harness (`/tmp/opencode/atelier/app_harness.js`) against the
  dev server + live backend: plan counts (DIS 29/8, Centrale 57/10,
  DCA 6/4, sidebar 98/34/4), zone-label projection and text fit, 2D
  hover/click + 3D raycast click opening the panel, provenance copy,
  Overview chips, zero console errors. Screenshots:
  `app_plan_dis.png`, `app_3d_dis.png`, `app_3d_panel.png`,
  `app_3d_dca.png`, `app_overview.png`.
- E2E smoke against the live backend through the vite dev proxy: app HTML,
  `/api/assets` (4 assets), `/api/simulate` for `leakage` (severity
  reaches 0.8, WARMUP samples null) and `healthy` (severity 0, no faults).
- Backend suite including `/api/simulate`: 19 API tests green.