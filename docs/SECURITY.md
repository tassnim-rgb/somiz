# Security posture (Phase 11)

Scope: this project is a **public demo of a simulated industrial digital
twin**. Every exposed number is SIMULATED; there is no real plant, no real
telemetry, and nothing here would ever be pointed at production equipment.
The security work in Phase 11 is about being honest and boring: no secrets
in the repository, validated inputs, reproducible scanning, and CI that
fails on a leaked key.

## 1. Secrets

- **None are committed.** The repository contains no API keys, tokens or
  credentials; `scripts/scan_secrets.py` verifies this automatically (exit
  0 = clean; see the sample run in section 4).
- `.env` is gitignored; `.env.example` ships placeholders only.
- `backend/env.py` loads an optional `.env` at startup with a strict
  precedence rule: **real environment variables always win over the file**,
  so a deployment's own secrets management (Vercel env vars, Docker
  secrets) can never be shadowed by a stray file.
- Scan the tracked files yourself: `python scripts/scan_secrets.py`. CI
  runs the same scanner and fails the build on any match.

## 2. Input validation

All API inputs are validated by FastAPI/Pydantic before reaching any code,
plus explicit guards in the ML/simulation core:

| Boundary | Behaviour |
| --- | --- |
| `asset_id` on create | `^[A-Za-z0-9_-]{1,32}$`; injection-style strings -> 422 |
| Unknown asset path | 404, never a 500 |
| `duration_s` (simulate) | `240..3600`, `NaN` / `Infinity` rejected (422) |
| `seed`, `stride` | int bounds enforced (422) |
| `limit` on measurements / diagnostics | `1..100_000` / `1..50_000` |
| Unknown JSON fields | ignored (safe leniency); never executed |
| Constant / all-NaN sensor data | handled explicitly (tests/test_edge_cases.py) |
| Zero-asset maintenance plan | empty schedule, zero cost (no crash) |

SQLAlchemy binds every value as a query parameter; there is no string-built
SQL in the codebase, so the injection-style requests in the test suite are
rejected by validation or resolve to a clean 404.

## 3. Honest boundaries (not claimed)

- The public API is **unauthenticated** and CORS is `*` for the local
  dashboard. Deliberate for a demo; never point it at real data.
- There is **no rate limiting**, **no audit log**, and no TLS of our own
  (terminated by Vercel at the edge).
- `POST /api/simulate` is pure compute; the seeded SQLite snapshot is
  read-only on Vercel Functions (see docs/DEPLOYMENT.md). Writes that
  persist require the Docker self-host path.
- Nothing in this document is a claim that the system is hardened for
  production. It is a demo with explicit, tested boundaries.

## 4. Tooling and CI

- `.github/workflows/ci.yml` runs the full pytest suite and the secret scan
  on every push to `digital-twin-platform` / `main`.
- If a real secret ever appears in this chat (e.g. a deployment token), it
  must be **revoked** at the issuer, not just deleted: secrets managers
  keep history.