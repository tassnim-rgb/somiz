"""Column schema shared by the data engine and the pipeline.

Single source of truth for the column names produced by the simulator
(simulation/simulator.py) and consumed/validated by the pipeline.
"""

from __future__ import annotations

# Sensor (measurement) columns in display units.
SENSOR_COLUMNS = [
    "vib", "t_motor", "t_fluid", "p_disch", "flow",
    "rpm", "current", "power", "efficiency",
]

# Physically-plausible ranges per sensor column (display units) used by
# validation. These are generic engineering bounds for the *default* pump
# archetype; real deployments must override them per asset.
RANGE_BOUNDS = {
    "vib":        (0.0, 30.0),    # mm/s RMS
    "t_motor":    (-20.0, 300.0), # °C
    "t_fluid":    (-20.0, 300.0), # °C
    "p_disch":    (0.0, 60.0),    # bar
    "flow":       (0.0, 300.0),   # m³/h
    "rpm":        (0.0, 2000.0),  # tr/min
    "current":    (0.0, 100.0),   # A
    "power":      (0.0, 100.0),   # kW
    "efficiency": (0.0, 100.0),   # %
}

# Columns that are not measurements (time, control, ground truth).
NON_SENSOR = {"t", "u"}
GROUND_TRUTH_COLUMNS = ["health_stage", "fault_severity", "dominant_fault"]
REQUIRED_COLUMNS = ["t", *SENSOR_COLUMNS, *GROUND_TRUTH_COLUMNS]


def is_sensor(col: str) -> bool:
    return col in SENSOR_COLUMNS


def is_ground_truth(col: str) -> bool:
    return col in GROUND_TRUTH_COLUMNS or col == "t" or col == "u" or col.startswith("d_")