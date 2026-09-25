"""Shared dependencies: database session and configuration access."""

from __future__ import annotations

import os

from .database import get_db  # noqa: F401  (re-exported for routers)

# Configuration constants are read from the environment at import time so
# nothing is hardcoded and no secrets live in the repository. There are no
# secrets in this project at all.
SOMIZ_DB = os.environ.get("SOMIZ_DB", "data/somiz.db")
SOMIZ_VERSION = os.environ.get("SOMIZ_VERSION", "0.1.0")


def app_version() -> str:
    return SOMIZ_VERSION