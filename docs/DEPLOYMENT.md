# Deployment (Phase 12, Vercel flavor)

This document describes how to publish a public URL for the SOMIZ platform.
The whole platform is SIMULATED; the deployed demo displays SIMULATED data
and says so on every page.

## Current status

Phase 12 in `PROJECT_AUDIT.md` is not complete. This file covers the Vercel
path that is prepared and ready to run; the audited alternative
(Docker Compose self-host) remains documented as the persistence-preserving
option.

## Preflight (done)

- [x] `vercel` CLI 60.0.1 installed (user space).
- [x] Frontend production build verified (`frontend/dist`, gzip ~1.6 MB).
- [x] `vercel.json`: Vercel Services (`web` = Vite static, `api` = FastAPI),
      top-level rewrites route `/api/*`, `/health`, `/docs`, `/openapi.json`
      to the API service and everything else to the SPA.
- [x] `requirements-vercel.txt`: slim runtime deps for the API service.
  The backend at request time imports only `simulation` + `digital_twin`
  (numpy/pandas) plus FastAPI/SQLAlchemy/Pydantic; the heavy stack
  (torch, shap, weasyprint, sklearn) is offline-only.
- [x] API service build command regenerates `data/somiz.db` deterministically
  (`seed_database.py --reset`, seed 42) so the function bundle always ships a
  current SIMULATED database. scipy + scikit-learn are installed in the build
  step for that reason and are not part of the runtime bundle.

## Deploy steps (need a logged-in Vercel account)

1. Authenticate once on this machine:

   ```bash
   vercel login          # opens a browser flow (needs your Vercel account)
   ```

2. Deploy from the repo root:

   ```bash
   vercel --prod
   ```

   On the first run Vercel asks to link/create the project. The project
   framework setting must be **Services** (Vercel dashboard or
   `vercel project add`), because the project combines two services.

3. Vercel builds each service, then prints the deployment URL, e.g.
   `https://somiz-<team>.vercel.app`.

## Honest constraints of the Vercel deployment

- **SQLite persistence.** Vercel Functions run on an ephemeral/read-only
  filesystem. The bundled `data/somiz.db` is a fixed SIMULATED snapshot:
  reads work, but writes (`POST /api/assets`, which exists for the demo)
  do not persist between invocations. The dashboard is effectively
  read-only online. `POST /api/simulate` is pure computation (no DB write)
  and works fully. For persistable writes, use the Docker self-host path.
- **Bundle size.** The API service ships numpy/pandas/pydantic/FastAPI plus
  the core packages; the DB snapshot is regenerated at build time.
- **No real telemetry.** The deployed product shows SIMULATED data only;
  connecting real data remains the placeholder documented in `.env.example`.
- **SPA deep links.** If navigating directly to a client route (for example
  `/assets/A00`) 404s after deploy, add an SPA-fallback rewrite for
  non-API paths to the `web` service (the catch-all `/(.*)` already aims at
  it; this is about how the static host resolves file-less paths).

## Alternative: Docker self-host (from the audit)

The audited Phase 12 approach keeps SQLite persistence:

```bash
# (Dockerfile + docker-compose.yml are not written yet; this is the plan)
# docker compose up --build   # builds backend + frontend, volumes for data/
```

Choose this instead of Vercel if persistence of created assets matters.

## Rollback

`vercel --prod` deploys to a unique URL per build; previous deployments
remain available in the dashboard and can be promoted back at any time.