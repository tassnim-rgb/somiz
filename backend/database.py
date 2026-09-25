"""SQLAlchemy setup: engine, session factory, declarative base.

The database lives at ``data/somiz.db`` by default (gitignored) and can
be overridden with the ``SOMIZ_DB`` environment variable. No credentials
are stored anywhere; there are no secrets in this project.
"""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Declarative base for all ORM models (backend.models)."""


def default_db_path() -> str:
    env = os.environ.get("SOMIZ_DB", "")
    if env:
        return env
    root = Path(__file__).resolve().parents[1]
    (root / "data").mkdir(exist_ok=True)
    return str(root / "data" / "somiz.db")


def build_engine(db_path: str | None = None):
    path = db_path or default_db_path()
    return create_engine(
        f"sqlite:///{path}",
        connect_args={"check_same_thread": False},
    )


engine = build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    """FastAPI dependency: one SQLAlchemy session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()