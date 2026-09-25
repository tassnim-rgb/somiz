"""ML layer: anomaly detection, evaluation, diagnosis, RUL, explainability."""

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
from .diagnosis import (
    HeuristicFaultClassifier,
    evaluate_classification,
    fault_labels,
)
from .rul import (
    GradientBoostingRUL,
    QuantileGradientBoostingRUL,
    RidgeRUL,
    WindowMLPRegressor,
    build_rul_target,
    evaluate_rul,
    interval_coverage,
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
    "HeuristicFaultClassifier",
    "evaluate_classification",
    "fault_labels",
    "GradientBoostingRUL",
    "QuantileGradientBoostingRUL",
    "RidgeRUL",
    "WindowMLPRegressor",
    "build_rul_target",
    "evaluate_rul",
    "interval_coverage",
]

__version__ = "0.1.0"