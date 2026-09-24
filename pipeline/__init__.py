"""Data pipeline: preprocessing, feature engineering, and leakage-safe
chronological splitting for time-series datasets produced by the simulator.

Every transformation is documented (see docs/DATA_GENERATION.md and the
``transform_log`` of Preprocessor). Data from the simulator is SIMULATED;
the pipeline itself is data-agnostic and would ingest real telemetry the
same way.
"""

from .schema import (
    GROUND_TRUTH_COLUMNS,
    RANGE_BOUNDS,
    REQUIRED_COLUMNS,
    SENSOR_COLUMNS,
    is_ground_truth,
    is_sensor,
)
from .split import chrono_split, expanding_window_cv
from .features import rate_of_change, rolling_features, spectral_features_frame
from .preprocess import PreprocessConfig, Preprocessor, ValidationReport

__all__ = [
    "GROUND_TRUTH_COLUMNS",
    "RANGE_BOUNDS",
    "REQUIRED_COLUMNS",
    "SENSOR_COLUMNS",
    "is_ground_truth",
    "is_sensor",
    "chrono_split",
    "expanding_window_cv",
    "rate_of_change",
    "rolling_features",
    "spectral_features_frame",
    "PreprocessConfig",
    "Preprocessor",
    "ValidationReport",
]

__version__ = "0.1.0"