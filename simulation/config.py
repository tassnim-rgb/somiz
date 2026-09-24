"""Configuration dataclasses for the digital-twin simulation.

All values are **SI internally** (angles rad, pressure Pa, flow m^3/s,
temperature degC, torque N*m, power W) unless stated otherwise. Display units
are applied at the sensor layer.

Units legend used across the package:
  rad, rad/s, N*m, Pa, m^3/s, m, kg, J/(kg*K), W, W/K, degC, A, V.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Physical machine
# ---------------------------------------------------------------------------


@dataclass
class MachineParams:
    """Lumped-parameter model of a motor-driven centrifugal pump.

    Unknown/company-specific values must be supplied by the platform owner;
    these defaults are a generic, physically-plausible small industrial pump
    set (documented in docs/MATHEMATICAL_MODEL.md).
    """

    # motor
    omega_sync: float = 157.08          # sync speed, rad/s (1500 rpm @ 50 Hz)
    omega_ref: float = 151.61           # rated operating speed, rad/s (~1448 rpm, 3.5% slip)
    tau_ref: float = 45.0               # rated shaft torque, N*m
    tau_max_ratio: float = 1.6          # breakdown torque / rated torque
    eta_motor: float = 0.90             # nominal motor efficiency (fraction)
    V_ll: float = 400.0                 # line-to-line voltage, V
    cos_phi: float = 0.85               # motor power factor

    # rotor dynamics + friction
    J: float = 0.8                      # rotor+impeller inertia, kg*m^2
    c_f: float = 0.02                   # viscous friction coeff, N*m*s/rad
    k_f: float = 2.0                    # wear gain on friction (tau_fric x(1+k_f*W))

    # centrifugal pump (affinity-law based)
    Q_ref: float = 0.02                 # rated flow, m^3/s (72 m^3/h)
    H_ref: float = 25.0                 # rated head, m
    rho: float = 1000.0                 # fluid density, kg/m^3
    p_suction: float = 0.0              # suction gauge pressure, Pa
    k_imp: float = 0.35                 # impeller-degradation factor on flow/head
    k_leak: float = 0.30                # leakage factor: Q_leak_max = k_leak*Q_ref*wn*d_leak
    k_block_flow: float = 0.55          # blockage effect on delivered flow
    k_block_head: float = 0.40          # blockage effect on discharge pressure

    # motor thermal
    C_m: float = 30e3                   # thermal mass, J/K
    hA_m: float = 25.0                  # thermal conductance to ambient, W/K
    k_overheat: float = 0.70            # cooling reduction at full overheat fault

    # fluid/process thermal
    C_f: float = 60e3                   # fluid thermal mass, J/K
    hA_f: float = 15.0                  # fluid<->ambient conductance, W/K
    c_p: float = 4180.0                 # fluid specific heat, J/(kg*K)
    T_in: float = 20.0                  # inlet fluid temperature, degC
    k_gen: float = 200.0                # parasitic heat into fluid, W

    # measurement dynamics
    tau_p: float = 0.5                  # discharge-pressure smoothing constant, s

    # environment
    T_amb: float = 25.0                 # ambient temperature, degC
    T_init: float = 25.0                # initial motor/fluid temperature, degC

    # vibration model coefficients (output signals, mm/s RMS)
    vib_base: float = 0.8               # baseline vibration at rated speed, mm/s
    vib_bearing: float = 3.2            # vibration growth with bearing wear
    vib_blockage: float = 2.0           # vibration growth with blockage
    vib_wear: float = 1.0               # vibration growth with global wear

    def validate(self) -> List[str]:
        """Return a list of physical-inconsistency messages (empty if OK)."""
        errs: List[str] = []
        if not self.omega_sync > 0:
            errs.append("omega_sync must be > 0")
        if not 0 < self.omega_ref < self.omega_sync:
            errs.append("require 0 < omega_ref < omega_sync")
        if not self.tau_ref > 0:
            errs.append("tau_ref must be > 0")
        if not self.tau_max_ratio > 1.0:
            errs.append("tau_max_ratio must be > 1.0")
        if not 0 < self.eta_motor <= 1.0:
            errs.append("eta_motor must be in (0, 1]")
        if not self.J > 0:
            errs.append("J must be > 0")
        if self.c_f < 0 or self.k_f < 0:
            errs.append("friction coefficients must be >= 0")
        if not self.Q_ref > 0 or not self.H_ref > 0:
            errs.append("Q_ref and H_ref must be > 0")
        if self.rho <= 0:
            errs.append("rho must be > 0")
        if not 0 <= self.k_imp <= 1 or not 0 <= self.k_leak <= 1:
            errs.append("degradation factors must be in [0, 1]")
        if not 0 <= self.k_block_flow <= 1 or not 0 <= self.k_block_head <= 1:
            errs.append("blockage factors must be in [0, 1]")
        if self.C_m <= 0 or self.hA_m < 0 or self.C_f <= 0:
            errs.append("thermal masses must be > 0, conductances >= 0")
        if not self.tau_p > 0:
            errs.append("tau_p must be > 0")
        return errs

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "MachineParams":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# ---------------------------------------------------------------------------
# Sensors
# ---------------------------------------------------------------------------


@dataclass
class SensorConfig:
    """Configuration of one observed channel.

    ``source`` names the physical output of the machine (see physics.py
    ``machine_outputs``), e.g. ``vibration_rms``, ``motor_temp``,
    ``discharge_pressure_bar``. ``scale`` is applied to the raw value for
    display; the SensorModel stores the *scaled* value (display units).
    """

    tag: str
    name: str                         # French label (UI) kept together with unit
    source: str                       # output key from the physics layer
    unit: str                         # display unit
    noise_std: float = 0.0            # additive Gaussian noise (display units)
    noise_rel: float = 0.0            # relative noise (fraction of value)
    drift_rate: float = 0.0           # additive linear drift per second (display units)
    missing_p: float = 0.0            # probability of missing sample (NaN)
    outlier_p: float = 0.0            # probability of outlier spike (5-10 sigma)
    outlier_sigma: float = 7.0
    lower: float = 0.0                # plausible lower bound (display units)
    upper: float = 1e12               # plausible upper bound (display units)


@dataclass
class SensorAnomaly:
    """A time-windowed sensor-level anomaly (not a physics fault)."""

    sensor_tag: str
    kind: str                         # 'drift' | 'stuck' | 'noise_burst' | 'outlier_burst'
    onset_s: float = 0.0
    duration_s: float = 0.0
    magnitude: float = 1.0            # drift rate multiplier / stuck fraction of last value


# ---------------------------------------------------------------------------
# Faults
# ---------------------------------------------------------------------------


@dataclass
class FaultSpec:
    """Physics-level degradation fault.

    ``fault_type`` must be one of the registered failure modes
    (see faults.py FAULT_TYPES): bearing, overheating, leakage, impeller,
    blockage, sensor_drift, sensor_stuck.

    Progression shapes:
      linear      d = target * clamp(t_on/duration, 0, 1)
      exponential d = target * (1 - exp(-k*t_on))   with k=5/duration
      step        d = target for t >= onset
    """

    fault_type: str
    onset_s: float = 0.0
    target: float = 1.0               # final severity 0..1
    duration_s: float = 0.0           # time from onset to target (0 => step)
    shape: str = "linear"
    label: str = ""


# ---------------------------------------------------------------------------
# Operating regime
# ---------------------------------------------------------------------------


@dataclass
class OperatingProfileSpec:
    """Piecewise-constant load profile for the drive: list of (t_end, u).

    u in [0, 1] is the load demand on the motor (1 = full demand).
    Startup and shutdown are modelled in physics via torque dynamics, so a
    ramp can be expressed with many small steps; defaults give a realistic
    warm-start/load-change/shutdown cycle.
    """

    segments: List[tuple] = field(default_factory=lambda: [])
    cycle: bool = False               # repeat the profile until sim end

    @staticmethod
    def default() -> "OperatingProfileSpec":
        return OperatingProfileSpec(
            segments=[
                (30, 0.60),     # startup ramp over 30 s
                (600, 0.60),    # steady, 60% load
                (660, 0.90),    # load step-up
                (1800, 0.90),   # high load
                (1860, 0.0),    # shutdown
                (2000, 0.0),    # off
                (2060, 0.60),   # restart
                (3600, 0.60),   # steady to end
            ],
            cycle=False,
        )


DEFAULT_PROFILE: OperatingProfileSpec = OperatingProfileSpec.default()


# ---------------------------------------------------------------------------
# Simulation config
# ---------------------------------------------------------------------------


class HealthStage(str, Enum):
    NORMAL = "NORMAL"
    EARLY = "EARLY"
    MODERATE = "MODERATE"
    SEVERE = "SEVERE"
    FAILURE = "FAILURE"


@dataclass
class SimulationConfig:
    """Everything needed to reproduce a simulation run."""

    seed: int = 42
    duration_s: float = 3600.0
    fs_hz: float = 1.0                # sensor sampling frequency
    dt_phys: float = 0.25             # physics sub-step (RK4)
    machine: MachineParams = field(default_factory=MachineParams)
    profile: OperatingProfileSpec = field(default_factory=OperatingProfileSpec.default)
    faults: List[FaultSpec] = field(default_factory=list)
    sensor_anomalies: List[SensorAnomaly] = field(default_factory=list)
    sensors: List[SensorConfig] = field(default_factory=list)
    stop_on_failure: bool = True      # shut the drive down if a fault reaches target>=1
    fault_stage_thresholds: Dict[str, float] = field(
        default_factory=lambda: {
            "EARLY": 0.05,
            "MODERATE": 0.30,
            "SEVERE": 0.60,
            "FAILURE": 0.90,
        }
    )

    def validate(self) -> List[str]:
        errs = list(self.machine.validate())
        if self.duration_s <= 0:
            errs.append("duration_s must be > 0")
        if not self.fs_hz > 0:
            errs.append("fs_hz must be > 0")
        if not self.dt_phys > 0:
            errs.append("dt_phys must be > 0")
        if not self.segments_cover():
            errs.append("profile does not cover the full duration; add segments or cycle=True")
        seen: set = set()
        for s in self.sensors:
            if s.tag in seen:
                errs.append(f"duplicate sensor tag {s.tag!r}")
            seen.add(s.tag)
        return errs

    def segments_cover(self) -> bool:
        if not self.profile.segments:
            return False
        if self.profile.cycle:
            return True
        last_end = 0.0
        for end, _u in self.profile.segments:
            last_end = max(last_end, end)
        # require a segment ending at >= duration
        return last_end >= self.duration_s - 1e-9

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SimulationConfig":
        known = set(cls.__dataclass_fields__)
        kwargs = {k: v for k, v in d.items() if k in known}
        if "machine" in d:
            kwargs["machine"] = MachineParams.from_dict(d["machine"])
        if "profile" in d and isinstance(d["profile"], dict):
            kwargs["profile"] = OperatingProfileSpec(**d["profile"])
        if "faults" in d:
            kwargs["faults"] = [FaultSpec(**f) for f in d["faults"]]
        if "sensor_anomalies" in d:
            kwargs["sensor_anomalies"] = [SensorAnomaly(**a) for a in d["sensor_anomalies"]]
        if "sensors" in d:
            kwargs["sensors"] = [SensorConfig(**s) for s in d["sensors"]]
        return cls(**kwargs)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


DEFAULT_MACHINE = MachineParams()


def default_sensor_set() -> List[SensorConfig]:
    """Display-unit sensor set for the rotating machine (French UI labels,
    English tags). Noise values are plausible for a well-installed instrument
    loop; they are configurable, not measured."""
    return [
        SensorConfig(tag="vib", name="Vibration", source="vibration_rms",
                     unit="mm/s", noise_std=0.04, missing_p=0.001, outlier_p=0.002),
        SensorConfig(tag="t_motor", name="Température moteur", source="motor_temp",
                     unit="°C", noise_std=0.3, drift_rate=0.0),
        SensorConfig(tag="t_fluid", name="Température procédé", source="fluid_temp",
                     unit="°C", noise_std=0.3),
        SensorConfig(tag="p_disch", name="Pression refoulement", source="discharge_pressure_bar",
                     unit="bar", noise_std=0.01, outlier_p=0.001),
        SensorConfig(tag="flow", name="Débit", source="flow_m3h",
                     unit="m³/h", noise_std=0.3, missing_p=0.001),
        SensorConfig(tag="rpm", name="Vitesse", source="speed_rpm",
                     unit="tr/min", noise_std=2.0),
        SensorConfig(tag="current", name="Courant moteur", source="motor_current_a",
                     unit="A", noise_std=0.15),
        SensorConfig(tag="power", name="Puissance", source="power_kw",
                     unit="kW", noise_std=0.04),
        SensorConfig(tag="efficiency", name="Rendement", source="efficiency",
                     unit="%", noise_std=0.15),
    ]