"""SOMIZ backend: FastAPI application.

Run after seeding (``python scripts/seed_database.py``):

    uvicorn backend.main:app --reload

REST + typed validation + OpenAPI docs at /docs. All data served is
SIMULATED / MODEL ASSUMPTION (see docs/API.md).
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .deps import app_version
from .routers import (
    assets_router,
    diagnostics_router,
    maintenance_router,
    meta_router,
    simulate_router,
)

app = FastAPI(
    title="SOMIZ digital twin API",
    version=app_version(),
    description=(
        "SIMULATED digital-twin backend for the motor-driven centrifugal "
        "pump fleet. Every value is a simulation or a model assumption; "
        "nothing here describes a real plant."
    ),
)

# Phase 8's dashboard runs on a different origin during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meta_router)
app.include_router(assets_router)
app.include_router(diagnostics_router)
app.include_router(maintenance_router)
app.include_router(simulate_router)