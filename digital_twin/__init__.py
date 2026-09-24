"""Digital-twin layer: health monitoring built on observed signals only.

The health index is a transparent, explainable quantity derived from sensor
deviations relative to a healthy baseline — never from the ground-truth
labels (which would be cheating). Its formula is documented in
docs/HEALTH_INDEX.md and it is validated against the simulator ground truth
in the experiment runner.
"""

from .health_index import HealthIndex, HealthIndexConfig, HealthIndexReport

__all__ = ["HealthIndex", "HealthIndexConfig", "HealthIndexReport"]

__version__ = "0.1.0"