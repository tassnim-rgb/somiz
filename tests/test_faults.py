"""Fault progression and health-stage tests."""

import numpy as np
import pytest

from simulation.config import FaultSpec, HealthStage
from simulation.faults import (
    FAULT_TO_PHYSICS,
    FAULT_TYPES,
    FaultManager,
    FaultStageModel,
)


def test_linear_progression():
    spec = FaultSpec(fault_type="bearing", onset_s=100, target=0.8, duration_s=200)
    fm = FaultManager([spec], seed=1)
    assert fm.progressions(50)["bearing"] == 0.0        # before onset
    assert fm.progressions(100)["bearing"] == 0.0       # at onset
    assert fm.progressions(200)["bearing"] == pytest.approx(0.4, abs=1e-9)
    assert fm.progressions(300)["bearing"] == pytest.approx(0.8, abs=1e-9)
    assert fm.progressions(500)["bearing"] == pytest.approx(0.8, abs=1e-9)  # clamped


def test_step_progression():
    spec = FaultSpec(fault_type="bearing", onset_s=10, target=1.0, duration_s=0, shape="step")
    fm = FaultManager([spec], seed=2)
    assert fm.progressions(9)["bearing"] == 0.0
    assert fm.progressions(10)["bearing"] == 1.0


def test_exponential_progression_bounded():
    spec = FaultSpec(fault_type="bearing", onset_s=0, target=0.9, duration_s=100, shape="exponential")
    fm = FaultManager([spec], seed=3)
    d = [fm.progressions(t)["bearing"] for t in np.linspace(0, 500, 50)]
    assert all(0.0 <= v <= 0.9 for v in d)
    assert d[-1] == pytest.approx(0.9, abs=1e-3)  # asymptotes to target


def test_duplicate_fault_types_rejected():
    with pytest.raises(ValueError):
        FaultManager([
            FaultSpec(fault_type="bearing"),
            FaultSpec(fault_type="bearing"),
        ], seed=1)


def test_physics_dict_mapping():
    fm = FaultManager([
        FaultSpec(fault_type="bearing", onset_s=0),
        FaultSpec(fault_type="leakage", onset_s=0),
    ], seed=4)
    d = fm.physics_dict(100)
    assert d.get("bearing") == 1.0
    assert d.get("leakage") == 1.0


def test_fault_catalogue_is_authored_for_all_physics_keys():
    for ftype in FAULT_TYPES:
        assert ftype in FAULT_TO_PHYSICS, f"{ftype} missing physics mapping"


def test_stage_mapping():
    sm = FaultStageModel({"EARLY": 0.05, "MODERATE": 0.30, "SEVERE": 0.60, "FAILURE": 0.90})
    cases = [(0.0, HealthStage.NORMAL), (0.04, HealthStage.NORMAL),
             (0.1, HealthStage.EARLY), (0.45, HealthStage.MODERATE),
             (0.75, HealthStage.SEVERE), (0.95, HealthStage.FAILURE), (2.0, HealthStage.FAILURE)]
    for d, expected in cases:
        assert sm.stage(d) == expected, f"d={d}"


def test_worst_stage_takes_maximum():
    sm = FaultStageModel({})
    assert sm.worst_stage({"bearing": 0.2, "leakage": 0.8}) == HealthStage.SEVERE


def test_worst_of_empty_is_normal():
    sm = FaultStageModel({})
    assert sm.worst_stage({}) == HealthStage.NORMAL


def test_active_faults_by_time():
    fm = FaultManager([FaultSpec(fault_type="bearing", onset_s=50)], seed=5)
    assert fm.active(10) == []
    assert len(fm.active(50)) == 1


def test_severity_target_clamped_to_unit():
    spec = FaultSpec(fault_type="bearing", onset_s=0, target=3.0, duration_s=10)
    fm = FaultManager([spec], seed=6)
    assert fm.progressions(100)["bearing"] <= 1.0