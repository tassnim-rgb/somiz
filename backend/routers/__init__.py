"""FastAPI routers package (backend/routers/)."""

from .assets import router as assets_router
from .diagnostics import router as diagnostics_router
from .maintenance import router as maintenance_router
from .meta import router as meta_router

__all__ = ["assets_router", "diagnostics_router", "maintenance_router", "meta_router"]