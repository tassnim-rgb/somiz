# SOMIZ Backend API (Phase 7)

The SIMULATED digital-twin platform exposes a REST API plus an OpenAPI
schema. **Every value served is a simulation or a model assumption. None
of it describes a real plant.** Label conventions from the project audit
apply: ground-truth-derived rows are marked `method=ground_truth_seed`,
model outputs carry a `model_version`, and any value that is not computed
is `null` rather than fabricated.

## Stack

- **FastAPI** (Python 3.11+) with Pydantic v2 request validation
- **SQLite via SQLAlchemy 2.x** (synchronous, `check_same_thread=False`)
- Auto-generated OpenAPI docs at `/docs` (Swagger UI) and `/openapi.json`
- No authentication, no API keys, no secrets in the repository: this is a
  local prototype backend. CORS is open for the Phase 8 dashboard origin.

## Run

```bash
python scripts/seed_database.py --reset   # create + populate data/somiz.db
uvicorn backend.main:app --reload        # dev server (default :8000)
```

Configuration is read from the environment only:

| Variable | Default | Meaning |
|---|---|---|
| `SOMIZ_DB` | `data/somiz.db` | SQLite file path (gitignored) |
| `SOMIZ_VERSION` | `0.1.0` | version string returned by `/health` |

## Database schema

Ten tables, mirroring `PROJECT_AUDIT.md` section 11.5 (PostgreSQL-ready:
no SQLite-specific features):

`assets`, `sensors`, `measurements`, `faults`, `anomalies`, `diagnoses`,
`predictions`, `maintenance_events`, `maintenance_plans`, `experiments`.

Seed contents (deterministic, 900 s simulated runs):

- 4 pump assets: `A00` healthy, `A01` bearing, `A02` leakage,
  `A03` blockage (fault onset at t=300 s)
- 9 sensors per asset, 32 436 measurement rows (dropouts flagged
  `MISSING`)
- 316 health-index predictions (Phase 4 index: `WARMUP` samples carry
  `null`, never a fabricated value) + 316 SIMULATED ground-truth
  diagnoses (`method=ground_truth_seed`)
- 724 statistical anomaly flags (RMS z-score, threshold 2.5,
  `false_alarm_flag` computed)
- 1 maintenance plan from the Phase 6 MILP scheduler + its events
  (objective: total cost, SIMULATED planning inputs)
- 3 experiment catalogue rows pointing at committed result artefacts

## Endpoints

### Meta

| Method | Path | Description |
|---|---|---|
| GET | `/health` | service + database status |
| GET | `/api/experiments` | experiment catalogue |

### Assets

| Method | Path | Description |
|---|---|---|
| GET | `/api/assets` | asset summaries |
| POST | `/api/assets` | create an asset (validated, 409 on duplicate) |
| GET | `/api/assets/{asset_id}` | full asset record |
| GET | `/api/assets/{asset_id}/sensors` | sensor catalogue |
| GET | `/api/assets/{asset_id}/measurements` | time series (query: `tag`, `limit` 1..100 000, `offset`) |

### Diagnostics

| Method | Path | Description |
|---|---|---|
| GET | `/api/assets/{asset_id}/diagnoses` | SIMULATED fault labels + `severity_estimate` |
| GET | `/api/assets/{asset_id}/predictions` | health index + RUL estimates |
| GET | `/api/assets/{asset_id}/anomalies` | anomaly flags with scores |

### Maintenance

| Method | Path | Description |
|---|---|---|
| GET | `/api/maintenance/plans?latest=true` | optimisation plans (MILP) |
| GET | `/api/maintenance/events` | all scheduled events |
| GET | `/api/assets/{asset_id}/maintenance-events` | per-asset events |

## Validation

Pydantic enforces input contracts on every endpoint:

- `asset_id` must match `^[A-Za-z0-9_-]+$`, 1..32 chars
- measurement `limit` must be in 1..100 000, `offset` >= 0
- invalid payloads return **422** before touching the database
- unknown assets return **404**; duplicate asset creation returns **409**

## Honest-label policy (how to read the rows)

- **predictions**: `health_index` is `null` during start-up warmup
  (t < 120 s) and on sensor dropout. `rul_lower`/`rul_upper`/`confidence`
  are `null` in the seed because the seed stores point estimates only;
  the Phase 5 quantile GBM produces real intervals for the streaming path.
- **diagnoses**: seeded from simulator ground truth and explicitly marked
  `method=ground_truth_seed`; the Phase 5 ML diagnosis models are the
  documented replacement.
- **maintenance plans**: produced by `scipy.optimize.milp` on SIMULATED
  planning inputs; `objective_value` is the planned total cost in EUR.

## Tests

`tests/test_backend.py` runs against a temporary database (never your
`data/somiz.db`): 16 API tests covering health, CRUD, validation, paging,
and the honest-label rules above.