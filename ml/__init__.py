"""ML layer: anomaly detection, evaluation, and (Phase 5) diagnosis/RUL."""

from .anomaly import (
    AnomalyDetector,
    StatisticalBaselineDetector,
    IsolationForestDetector,
    PointAutoencoderDetector,
    WindowedAutoencoderDetector,
)
from .evaluate import (
    DetectionMetrics,
    at_far_target,
    best_by_f1,
    build_metrics,
    persist_flags,
    threshold_sweep,
)

__all__ = [
    "AnomalyDetector",
    "StatisticalBaselineDetector",
    "IsolationForestDetector",
    "PointAutoencoderDetector",
    "WindowedAutoencoderDetector",
    "DetectionMetrics",
    "at_far_target",
    "best_by_f1",
    "build_metrics",
    "persist_flags",
    "threshold_sweep",
]

__version__ = "0.1.0"