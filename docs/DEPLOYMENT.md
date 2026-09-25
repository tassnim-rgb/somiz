# Deployment (Phase 12, Vercel)

SOMIZ is live at **https://somiz.vercel.app** (production alias of
`somiz-<hash>-nebula-89ad.vercel.app`). The whole platform is SIMULATED; every
page and endpoint says so.

## Architecture on Vercel (Services, one domain)

- `web` service — `frontend/`, Vite preset: `npm run build` → static SPA at `/`.
- `api` service — root `.`, FastAPI preset, entrypoint `backend.main:app`,
  with a slim runtime dependency set (`requirements-vercel.txt`).
  `vercel.json` top-level rewrites route `/api/*`, `/health`, `/docs`,
  `/openapi.json` to the API service and everything else to the SPA.

```json
{
  "services": {
    "web": { "root": "frontend/", "framework": "vite" },
    "api": {
      "root": ".",
      "framework": "fastapi",
      "entrypoint": "backend.main:app",
      "installCommand": "pip install -r requirements-vercel.txt",
      "buildCommand": "uv venv /tmp/somiz-seedenv && uv pip install --python /tmp/somiz-seedenv/bin/python --quiet numpy pandas sqlalchemy 'scipy>=1.14' 'scikit-learn>=1.5' && /tmp/somiz-seedenv/bin/python scripts/seed_database.py --reset"
    }
  },
  "rewrites": [
    { "source": "/api/(.*)", "destination": { "service": "api" } },
    { "source": "/health", "destination": { "service": "api" } },
    { "source": "/docs", "destination": { "service": "api" } },
    { "source": "/openapi.json", "destination": { "service": "api" } },
    { "source": "/(.*)", "destination": { "service": "web" } }
  ]
}
```

## Why the pieces are shaped this way

- **Slim runtime deps** (`requirements-vercel.txt`): the API at request time
  imports only `simulation` + `digital_twin` (numpy/pandas) plus
  FastAPI/SQLAlchemy/Pydantic. The heavy stack (torch, shap, weasyprint,
  sklearn) is offline-only. `ml/anomaly.py` guards its torch import so the
  package imports without it; only the PyTorch autoencoder detectors require
  torch, and they raise a clear error if used without it.
- **Seed isolated in /tmp**: `seed_database.py` needs scipy + scikit-learn,
  but only at build time. Running it from a throwaway `uv` environment
  (`/tmp/somiz-seedenv`) keeps the service venv slim enough that the function
  bundle stays under the 225 MB limit (a custom install command disables
  Vercel's automatic bundle optimization, so everything in the venv ships).
- **`.vercelignore` not `.gitignore`**: the Vercel CLI does not reliably
  honor the gitignore for uploads. Landing ~62 MB of `data/generated` +
  `frontend/dist` + the DB on the upload. The `.vercelignore` excludes
  artifact **directories** only. Never add blanket `*.html` rules: they also
  exclude `frontend/index.html`, the Vite entry, and break the web build with
  `[UNRESOLVED_ENTRY]`.
- **IPv4 workaround for the CLI**: this machine has no working IPv6 route
  (NAT64 resolves but times out ~50 % of the time with Node's fetch). Deploy
  with `NODE_OPTIONS="--dns-result-order=ipv4first --no-network-family-autoselection"`.

## Deploy command (from this machine)

```bash
export PATH="$HOME/.local/pkg/git-local/usr/git-core:$HOME/.local/pkg/git-local/usr/bin:$HOME/.local/pkg/node/bin:$HOME/.local/bin:$PATH"
export GIT_EXEC_PATH="$HOME/.local/pkg/git-local/usr/lib/git-core"
export VERCEL_TELEMETRY_DISABLED=1
export NODE_OPTIONS="--dns-result-order=ipv4first --no-network-family-autoselection"
vercel deploy --prod --yes --token "$TOKEN"
```

The project (`somiz`, team `nebula-89ad`) is already linked via `.vercel/project.json`.

## Verified live (2026-09-25)

| Endpoint | Result |
| --- | --- |
| `https://somiz.vercel.app/` | 200, SPA |
| `/health` | 200 JSON |
| `/api/assets` | 200, A00–A03 (SIMULATED pumps) |
| `/openapi.json`, `/docs` | 200 |
| POST `/api/simulate` | 200, SIMULATED series + health index |

## Honest constraints of this deployment

- **SQLite is a fixed snapshot.** Vercel Functions run on an ephemeral,
  effectively read-only filesystem. `data/somiz.db` is generated at build time
  and bundled read-only: reads work, but writes (`POST /api/assets`) do not
  persist between invocations. The deployed dashboard is read-only online.
  `POST /api/simulate` is pure computation (no DB write) and works fully.
  For persistable writes use the Docker self-host path below.
- **No real telemetry.** The deployed product shows SIMULATED data only;
  connecting real data remains the placeholder in `.env.example`.
- **Token hygiene.** The deploy token must be revoked after use
  (vercel.com/account/tokens). It grants full account access.

## Future: Docker self-host (persistent)

The audited Phase 12 alternative keeps SQLite persistence:

```bash
# (Dockerfile + docker-compose.yml not written yet; this is the plan)
# docker compose up --build   # backend + frontend, volume for data/
```

Choose this instead of Vercel if persistence of created assets matters.

## Rollback

Every `vercel --prod` deploy is immutable and remains available in the
dashboard; promote any previous deployment back at any time.