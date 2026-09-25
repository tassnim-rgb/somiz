"""Minimal .env loader for the SOMIZ backend.

Reads KEY=VALUE lines from ``.env`` (repo root by default) and exports them
into the process environment WITHOUT overriding variables that are already
set, so a real shell export always wins over the file. No external
dependency. Secrets never belong in the repository; the loader only makes
opt-in local configuration possible (see docs/SECURITY.md and
scripts/scan_secrets.py).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional


def parse_dotenv(text: str) -> Dict[str, str]:
    """Parse dotenv-style text into ``{KEY: value}``.

    Rules: ``#`` comments and blank lines are ignored; an optional leading
    ``export `` is stripped; the first ``=`` splits key and value; an
    optional surrounding single/double quote pair is stripped from the value.
    """
    out: Dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        out[key] = value
    return out


def load_dotenv(path: Optional[Path] = None) -> Dict[str, str]:
    """Load ``.env`` into ``os.environ`` if the file exists.

    Existing environment variables are never overridden. Returns the
    ``{KEY: value}`` pairs that were actually applied.
    """
    if path is None:
        path = Path(__file__).resolve().parents[1] / ".env"
    if not path.is_file():
        return {}
    applied: Dict[str, str] = {}
    for key, value in parse_dotenv(path.read_text(encoding="utf-8")).items():
        if key not in os.environ:
            os.environ[key] = value
            applied[key] = value
    return applied