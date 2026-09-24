"""Reproducible dataset generation for the digital-twin platform.

Given a master seed, a set of asset scenarios and a destination directory,
the generator simulates every asset deterministically, exports CSV/Parquet,
and writes a manifest JSON so any dataset can be traced to its generating
configuration (provenance). Everything generated here is SIMULATED data.
"""

from .generator import AssetRunSpec, DatasetGenerator, Manifest, SCENARIOS, default_fleet

__all__ = ["AssetRunSpec", "DatasetGenerator", "Manifest", "SCENARIOS", "default_fleet"]

__version__ = "0.1.0"