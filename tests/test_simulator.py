"""End-to-end simulator tests: determinism, ground truth, failure scenarios,
edge cases, export."""

import numpy as np
import pandas as pd
import pytest

from simulation.config import (
    FaultSpec,
    OperatingProfileSpec,
    SensorAnomaly,
    SensorConfig,
    SimulationConfig,
)
from simulation.simulator import Simulator


def _short_profile(last=600.0) -> OperatingProfileSpec:
    if last <= 60:
        return OperatingProfileSpec(segments=[(float(last), 0.6)], cycle=False)
    return OperatingProfileSpec(segments=[(60, 0.6), (last, 0.9)], cycle=False)


def _base_cfg(duration=300.0, **kw) -> SimulationConfig:
    kw.setdefault("seed", 42)
    return SimulationConfig(
        duration_s=duration,
        fs_hz=1.0,
        dt_phys=0.1,
        profile=_short_profile(last=duration),
        **kw,
    )


FAIL_FAULT = FaultSpec(fault_type="bearing", onset_s=50, target=1.0, duration_s=100)


# ---------------------------------------------------------------------
# Determinism and structure
# ---------------------------------------------------------------------


def test_same_seed_identical_run():
    a = Simulator(_base_cfg()).run()
    b = Simulator(_base_cfg()).run()
    pd.testing.assert_frame_equal(a.df, b.df)
    assert a.meta["seed"] == b.meta["seed"] == 42


def test_different_seed_changes_noise_but_not_structure():
    a = Simulator(_base_cfg(seed=1)).run()
    b = Simulator(_base_cfg(seed=2)).run()
    assert not a.df["vib"].equals(b.df["vib"])
    assert a.df["health_stage"].equals(b.df["health_stage"])  # physics identical


def test_frame_shape_and_columns():
    fr = Simulator(_base_cfg(duration=100.0)).run()
    assert fr.n_samples == 101
    for col in ["t", "vib", "t_motor", "flow", "health_stage", "fault_severity",
                "dominant_fault", "u"]:
        assert col in fr.df.columns
    assert (fr.df["t"].diff().dropna() > 0).all()  # timestamps increasing


def test_meta_is_self_describing():
    fr = Simulator(_base_cfg()).run()
    assert fr.meta["simulated"] is True
    assert "config" in fr.meta and "fault_timeline" in fr.meta
    import json
    json.dumps(fr.meta)  # serialisable


# ---------------------------------------------------------------------
# Ground truth behaviour
# ---------------------------------------------------------------------


def test_no_fault_run_stays_normal():
    fr = Simulator(_base_cfg()).run()
    assert set(fr.df["health_stage"].unique()) == {"NORMAL"}
    assert (fr.df["dominant_fault"] == "").all()
    assert (fr.df["fault_severity"] == 0.0).all()


def test_bearing_fault_progresses_through_stages():
    cfg = _base_cfg(duration=300.0, faults=[FAIL_FAULT])
    fr = Simulator(cfg).run()
    stages = fr.df["health_stage"].unique()
    assert "NORMAL" in stages
    assert "FAILURE" in stages
    assert "SEVERE" in stages


def test_progressive_vibration_increase_with_bearing_wear():
    # stop_on_failure off so we observe pure degradation growth
    cfg = _base_cfg(duration=300.0, faults=[FAIL_FAULT], stop_on_failure=False)
    df = Simulator(cfg).run().df
    early = df.loc[df["t"] <= 60, "vib"].mean()
    late = df.loc[(df["t"] >= 120) & (df["t"] <= 145), "vib"].mean()
    assert late > early * 1.5


def test_stop_on_failure_shuts_drive_down():
    cfg = _base_cfg(duration=300.0, faults=[FAIL_FAULT], stop_on_failure=True)
    df = Simulator(cfg).run().df
    t_stop = df.loc[df["fault_severity"] >= 1.0, "t"].min()
    after = df.loc[df["t"] > t_stop + 5]
    assert (after["u"] == 0.0).all()
    assert after["t_motor"].iloc[-1] < after["t_motor"].iloc[0] + 1e-6 or \
        after["t_motor"].iloc[-1] < 80  # cooling after stop


def test_dominant_fault_tracks_maximum():
    cfg = _base_cfg(
        duration=300.0,
        faults=[FaultSpec("leakage", onset_s=40, target=0.6, duration_s=80),
                FAIL_FAULT],
    )
    df = Simulator(cfg).run().df
    # after bearing passes leakage severity the dominant must flip to bearing
    flipping = df[(df["d_bearing"] > df["d_leakage"])]
    assert (flipping["dominant_fault"] == "bearing").all()


def test_simultaneous_faults_all_recorded():
    cfg = _base_cfg(
        duration=200.0,
        faults=[
            FaultSpec("bearing", onset_s=30, target=0.8, duration_s=100),
            FaultSpec("leakage", onset_s=60, target=0.7, duration_s=80),
            FaultSpec("impeller", onset_s=90, target=0.5, duration_s=60),
        ],
    )
    df = Simulator(cfg).run().df
    for col in ["d_bearing", "d_leakage", "d_impeller"]:
        assert (df[col] >= 0.0).all() and (df[col] <= 1.0).all()


# ---------------------------------------------------------------------
# Sensor edge cases at the simulator level
# ---------------------------------------------------------------------


def test_missing_sensor_yields_nan_not_crash():
    from simulation.config import default_sensor_set
    sensors = default_sensor_set()
    sensors = [s for s in sensors if s.tag != "vib"]
    vib = SensorConfig(tag="vib", name="Vibration", source="vibration_rms",
                       unit="mm/s", missing_p=1.0)
    cfg = _base_cfg(duration=50.0, sensors=[*sensors, vib])
    fr = Simulator(cfg).run()
    assert fr.df["vib"].isna().all()
    assert fr.df["health_stage"].notna().all()  # ground truth unaffected
    assert fr.df["flow"].notna().any()


def test_sensor_stuck_window_retains_constant_value():
    anom = SensorAnomaly(sensor_tag="flow", kind="stuck", onset_s=20, duration_s=30)
    cfg = _base_cfg(duration=100.0, sensor_anomalies=[anom])
    df = Simulator(cfg).run().df
    window = df[(df["t"] >= 20) & (df["t"] < 50)]
    # underlying flow is slowly varying; stuck => near-identical values
    assert window["flow"].nunique() <= 2  # captured value + rounding


def test_total_degradation_flow_near_zero_blocked_discharge():
    cfg = _base_cfg(
        duration=100.0,
        faults=[FaultSpec("blockage", onset_s=10, target=1.0, duration_s=5)],
    )
    df = Simulator(cfg).run().df
    late = df[df["t"] > 40]
    assert late["flow"].mean() < df[df["t"] < 10]["flow"].mean() * 0.5


# ---------------------------------------------------------------------
# Config validation edge cases
# ---------------------------------------------------------------------


def test_profile_must_cover_duration():
    cfg = SimulationConfig(
        seed=1, duration_s=1000.0, fs_hz=1.0,
        profile=OperatingProfileSpec(segments=[(100, 0.6)], cycle=False),
    )
    assert cfg.validate()  # non-empty errors
    with pytest.raises(ValueError):
        Simulator(cfg)


def test_bad_machine_rejected():
    cfg = _base_cfg()
    cfg.machine.J = -5.0
    with pytest.raises(ValueError):
        Simulator(cfg)


def test_zero_or_negative_duration_rejected():
    for bad in [0.0, -10.0]:
        cfg = _base_cfg(duration=bad)
        with pytest.raises(ValueError):
            Simulator(cfg)


def test_bad_profile_segment_rejected():
    from simulation.config import OperatingProfileSpec
    from simulation.regimes import profile_from_spec
    with pytest.raises(ValueError):
        profile_from_spec(OperatingProfileSpec(segments=[(-5, 0.6)]))
    with pytest.raises(ValueError):
        profile_from_spec(OperatingProfileSpec(segments=[(10, 1.5)]))
    with pytest.raises(ValueError):
        profile_from_spec(OperatingProfileSpec(segments=[(20, 0.5), (10, 0.5)]))


def test_duplicate_sensor_tags_rejected():
    from simulation.config import default_sensor_set
    cfg = _base_cfg()
    dup = SensorConfig(tag="vib", name="x", source="vibration_rms", unit="mm/s")
    cfg.sensors = default_sensor_set() + [dup]
    with pytest.raises(ValueError):
        Simulator(cfg)


def test_duplicate_fault_types_rejected_by_simulator():
    cfg = _base_cfg(faults=[FaultSpec("bearing", onset_s=10), FaultSpec("bearing", onset_s=20)])
    with pytest.raises(ValueError):
        Simulator(cfg)


# ---------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------


def test_csv_roundtrip(tmp_path):
    fr = Simulator(_base_cfg(duration=30.0)).run()
    p = tmp_path / "run.csv"
    fr.to_csv(str(p))
    back = pd.read_csv(p, keep_default_na=False)  # preserve '' (empty dominant_fault)
    pd.testing.assert_frame_equal(fr.df, back, check_dtype=False)


def test_parquet_roundtrip(tmp_path):
    fr = Simulator(_base_cfg(duration=30.0)).run()
    p = tmp_path / "run.parquet"
    fr.to_parquet(str(p))
    back = pd.read_parquet(p)
    pd.testing.assert_frame_equal(fr.df, back)


def test_config_json_roundtrip():
    cfg = _base_cfg(faults=[FAIL_FAULT])
    cfg2 = SimulationConfig.from_dict(cfg.to_dict())
    assert cfg2.seed == cfg.seed
    assert cfg2.machine.omega_ref == cfg.machine.omega_ref
    assert cfg2.faults[0].fault_type == "bearing"


# ---------------------------------------------------------------------
# Data sanity (simulation is plausible, not garbage)
# ---------------------------------------------------------------------


def test_running_machine_produces_plausible_ranges():
    cfg = _base_cfg(duration=120.0)
    df = Simulator(cfg).run().df
    running = df[df["t"] > 15]
    assert running["rpm"].median() > 1000        # up near rated 1450 rpm
    assert running["flow"].median() > 0          # pumping
    assert (running["rpm"] < 1600).all()
    assert (running["t_motor"] > 20).all()       # above ambient
    assert running["p_disch"].median() > 1.0     # bar, above suction
    assert running["vib"].median() > 0.0


def test_efficiency_column_in_physical_range():
    cfg = _base_cfg(duration=120.0)
    df = Simulator(cfg).run().df
    eff = df[(df["t"] > 15) & (df["u"] > 0)]["efficiency"]
    assert (eff >= 0.0).all() and (eff <= 100.0).all()
    assert eff.median() > 5.0  # not trivially zero while running