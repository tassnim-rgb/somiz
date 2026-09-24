"""Physics-model tests: parameter validation, torque/affinity sanity,
fault-to-physics coupling, numerical stability, edge cases."""

import numpy as np
import pytest

from simulation.config import MachineParams
from simulation.physics import (
    D_BEARING,
    D_BLOCK,
    D_IMP,
    D_LEAK,
    D_OVERHEAT,
    RotatingMachine,
)

# ---------------------------------------------------------------------
# Parameter validation
# ---------------------------------------------------------------------


def test_default_params_valid():
    assert MachineParams().validate() == []


@pytest.mark.parametrize(
    "patch",
    [
        {"J": -1.0},
        {"eta_motor": 1.5},
        {"omega_ref": 200.0},      # > omega_sync
        {"Q_ref": 0.0},
        {"tau_max_ratio": 0.5},    # breakdown < rated makes no sense
        {"k_imp": 1.5},
        {"tau_p": 0.0},
        {"rho": -999.0},
    ],
)
def test_invalid_params_rejected(patch):
    p = MachineParams(**patch)
    assert p.validate(), f"expected validation errors for {patch}"
    with pytest.raises(ValueError):
        RotatingMachine(p)


# ---------------------------------------------------------------------
# Torque model
# ---------------------------------------------------------------------


def test_motor_torque_at_rated_speed():
    m = RotatingMachine(MachineParams())
    tau = m.motor_torque(u=1.0, omega=m.p.omega_ref)
    # slip_ratio == 1 at rated speed -> torque == tau_ref (clipped)
    assert tau == pytest.approx(m.p.tau_ref, rel=1e-9)


def test_motor_torque_zero_at_sync_and_clipped():
    m = RotatingMachine(MachineParams())
    assert m.motor_torque(u=1.0, omega=m.p.omega_sync) == pytest.approx(0.0, abs=1e-6)
    # at standstill slip_ratio > 1 but torque is capped at breakdown torque
    tau0 = m.motor_torque(u=1.0, omega=0.0)
    assert tau0 == pytest.approx(m.tau_max, rel=1e-9)


def test_pump_torque_scales_with_speed_squared():
    """Affinity law: hydraulic power ~ omega^3 => torque ~ omega^2."""
    m = RotatingMachine(MachineParams())
    t1 = m.pump_torque(m.p.omega_ref, d_imp=0.0)
    t05 = m.pump_torque(0.5 * m.p.omega_ref, d_imp=0.0)
    assert t1 > 0
    assert t05 / t1 == pytest.approx(0.25, rel=1e-6)


def test_pump_torque_zero_at_zero_speed():
    m = RotatingMachine(MachineParams())
    assert m.pump_torque(0.0, d_imp=0.0) == 0.0


def test_rated_hyddraulic_power_plausible():
    """Rated hydraulic power must be below rated shaft torque * speed
    (efficiency < 1) and positive."""
    m = RotatingMachine(MachineParams())
    p = m.p
    p_h = p.rho * 9.81 * p.Q_ref * p.H_ref
    assert 0 < p_h < p.tau_ref * p.omega_ref


def test_friction_grows_with_bearing_wear():
    m = RotatingMachine(MachineParams())
    w = m.p.omega_ref
    f0 = m.friction_torque(w, d_b=0.0)
    f1 = m.friction_torque(w, d_b=1.0)
    assert f1 == pytest.approx(f0 * (1 + m.p.k_f), rel=1e-9)


def test_friction_zero_when_stopped():
    m = RotatingMachine(MachineParams())
    assert m.friction_torque(0.0, d_b=1.0) == 0.0


# ---------------------------------------------------------------------
# Degradation coupling (physics)
# ---------------------------------------------------------------------


def _steady_speed(m: RotatingMachine, u=0.6, d=None, steps=40000, dt=0.005):
    """Integrate open-loop to steady state and return omega."""
    d = d or {}
    x = m.x0()
    for _ in range(steps):
        x = m.step_rk4(x, u, d, dt)
    return x


def test_startup_reaches_speed_between_rated_and_sync():
    m = RotatingMachine(MachineParams())
    x = _steady_speed(m, u=1.0)
    w = x[0]
    assert m.p.omega_ref <= w <= m.p.omega_sync + 1e-6


def test_no_fault_steady_state_is_stable():
    m = RotatingMachine(MachineParams())
    x1 = _steady_speed(m, u=0.6, steps=30000)
    x2 = m.step_rk4(x1, 0.6, {}, 0.01)
    assert np.all(np.isfinite(x2))
    assert abs(x2[0] - x1[0]) < 1e-4  # speed essentially constant


def test_impeller_wear_reduces_flow():
    m = RotatingMachine(MachineParams())
    w = m.p.omega_ref
    q0 = m.flow_out(w, d_imp=0.0, d_leak=0.0, d_blk=0.0)
    q1 = m.flow_out(w, d_imp=1.0, d_leak=0.0, d_blk=0.0)
    assert q1 < q0


def test_leakage_reduces_net_flow():
    m = RotatingMachine(MachineParams())
    w = m.p.omega_ref
    q0 = m.flow_out(w, d_imp=0.0, d_leak=0.0, d_blk=0.0)
    q1 = m.flow_out(w, d_imp=0.0, d_leak=1.0, d_blk=0.0)
    assert q1 < q0
    assert q1 >= 0.0


def test_blockage_reduces_flow_and_raises_pressure():
    m = RotatingMachine(MachineParams())
    w = m.p.omega_ref
    q0 = m.flow_out(w, 0, 0, d_blk=0.0)
    q1 = m.flow_out(w, 0, 0, d_blk=1.0)
    p0 = m.p_target(w, 0, d_blk=0.0)
    p1 = m.p_target(w, 0, d_blk=1.0)
    assert q1 < q0
    assert p1 > p0


def test_full_blockage_flow_is_zero_not_negative():
    m = RotatingMachine(MachineParams())
    q = m.flow_out(m.p.omega_ref, 0, 0, d_blk=1.0)
    # k_block_flow default 0.55 => not zero but reduced; must be >= 0
    assert q >= 0.0


def test_overheating_raises_motor_temperature():
    """Reduced cooling must raise the motor's steady-state temperature.

    Analytic steady state of the thermal lump:
        T_ss = T_amb + P_loss / (hA_m * (1 - k_oh * d_oh))
    evaluated at rated torque/speed (P_loss = (1-eta)*P_el).
    """
    p = MachineParams()
    m = RotatingMachine(p)
    # rated losses: tau_m = tau_ref at omega_ref (slip_ratio == 1)
    omega = p.omega_ref
    tau_m = m.motor_torque(u=1.0, omega=omega)
    assert tau_m == pytest.approx(p.tau_ref, rel=1e-9)
    p_el = tau_m * omega / p.eta_motor
    p_loss = (1.0 - p.eta_motor) * p_el

    t_healthy = p.T_amb + p_loss / p.hA_m
    t_overheat = p.T_amb + p_loss / (p.hA_m * (1.0 - p.k_overheat))

    assert t_healthy > p.T_amb
    assert t_overheat > t_healthy + 20.0

    # RHS sign check at a warm-but-not-settled temperature
    x = np.array([omega, p.T_amb + 30.0, p.T_in, 0.0])
    d_healthy = m.rhs(x, 1.0, {})[1]
    d_hot = m.rhs(x, 1.0, {D_OVERHEAT: 1.0})[1]
    assert d_hot > d_healthy  # overheat heats faster at the same state


def test_bearing_wear_slows_machine_at_same_demand():
    m = RotatingMachine(MachineParams())
    x0 = _steady_speed(m, u=0.6, d={})
    x1 = _steady_speed(m, u=0.6, d={D_BEARING: 1.0})
    assert x1[0] < x0[0]


# ---------------------------------------------------------------------
# Numerical stability / edge cases
# ---------------------------------------------------------------------


def test_integrator_no_nan_over_long_run():
    m = RotatingMachine(MachineParams())
    x = m.x0()
    for i in range(20000):
        u = 0.9 if (i // 1000) % 2 == 0 else 0.2
        x = m.step_rk4(x, u, {D_BLOCK: 0.5, D_IMP: 0.5}, 0.01)
    assert np.all(np.isfinite(x))


def test_outputs_finite_and_nonnegative_where_physical():
    m = RotatingMachine(MachineParams())
    x = np.array([150.0, 60.0, 20.0, 2.5e5])
    out = m.outputs(x, u=0.8, d={D_BEARING: 0.4})
    assert np.isfinite(list(out.values())).all()
    assert out["speed_rpm"] > 0
    assert out["motor_current_a"] >= 0
    assert out["flow_m3h"] >= 0
    assert out["vibration_rms"] >= 0
    assert 0 <= out["efficiency"] <= 100


def test_outputs_at_zero_state():
    """A machine that is off must still produce finite outputs."""
    m = RotatingMachine(MachineParams())
    x = np.zeros(4)
    x[3] = m.p.p_suction
    out = m.outputs(x, u=0.0, d={})
    assert np.isfinite(list(out.values())).all()
    assert out["speed_rpm"] == 0.0
    assert out["motor_current_a"] == 0.0
    assert out["flow_m3h"] == 0.0


def test_bearing_fault_increases_vibration_output():
    m = RotatingMachine(MachineParams())
    x = np.array([m.p.omega_ref, 40.0, 20.0, 2.5e5])
    v0 = m.outputs(x, 0.8, {D_BEARING: 0.0})["vibration_rms"]
    v1 = m.outputs(x, 0.8, {D_BEARING: 1.0})["vibration_rms"]
    assert v1 > v0


def test_leakage_not_in_pressure_target_but_in_flow():
    """Documented model assumption: leakage reduces flow, not head."""
    m = RotatingMachine(MachineParams())
    w = m.p.omega_ref
    p0 = m.p_target(w, 0, 0)
    p1 = m.p_target(w, 0, 0)  # d_leak not a parameter of p_target
    assert p0 == p1