"""SOMIZ backend: FastAPI application.

Run after seeding (``python scripts/seed_database.py``):

    uvicorn backend.main:app --reload

REST + typed validation + OpenAPI docs at /docs. All data served is
SIMULATED / MODEL ASSUMPTION (see docs/API.md).
"""

from __future__ import annotations

import math

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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


def _json_safe(value):
    """False for non-finite floats, which JSON cannot represent."""
    return not isinstance(value, float) or math.isfinite(value)


async def _handle_validation_error(request: Request,
                                   exc: RequestValidationError):
    """Always answer 422, even when the offending input was a non-finite
    float literal (NaN / Infinity). Those are rejected by validation, but
    the error detail must stay JSON-serialisable instead of crashing the
    response renderer (Phase 11 hardening)."""
    errors = []
    for e in exc.errors():
        safe = {k: v for k, v in e.items()
                if k != "input" or _json_safe(v)}
        ctx = safe.get("ctx")
        if isinstance(ctx, dict):
            safe["ctx"] = {k: v for k, v in ctx.items() if _json_safe(v)}
        errors.append(safe)
    return JSONResponse(status_code=422, content={"detail": errors})


app.add_exception_handler(RequestValidationError, _handle_validation_error)

app.include_router(meta_router)
app.include_router(assets_router)
app.include_router(diagnostics_router)
app.include_router(maintenance_router)
app.include_router(simulate_router)