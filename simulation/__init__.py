"""Simulation package: physics-based industrial asset models and a synthetic
sensor data engine.

This is the Phase 2 core of the SOMIZ digital-twin platform. Everything here
is a **simulation**; no real plant data is claimed. The asset model is a
generic, configurable motor-driven centrifugal pump (rotating machine
archetype) whose parameters can later be replaced by real company data.
"""

from .config import (
    MachineParams,
    SensorConfig,
    SensorAnomaly,
    FaultSpec,
    OperatingProfileSpec,
    SimulationConfig,
    HealthStage,
    DEFAULT_MACHINE,
    DEFAULT_PROFILE,
)
from .physics import RotatingMachine, machine_outputs
from .faults import FaultManager, FaultStageModel, fault_from_spec
from .regimes import OperatingProfile, profile_from_spec
from .sensors import SensorModel, sensor_from_config
from .simulator import Simulator, MeasurementFrame

__all__ = [
    "MachineParams",
    "SensorConfig",
    "SensorAnomaly",
    "FaultSpec",
    "OperatingProfileSpec",
    "SimulationConfig",
    "HealthStage",
    "DEFAULT_MACHINE",
    "DEFAULT_PROFILE",
    "RotatingMachine",
    "machine_outputs",
    "FaultManager",
    "FaultStageModel",
    "fault_from_spec",
    "OperatingProfile",
    "profile_from_spec",
    "SensorModel",
    "sensor_from_config",
    "Simulator",
    "MeasurementFrame",
]

__version__ = "0.2.0"