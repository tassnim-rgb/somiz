"""Physics-informed lumped-parameter model of a motor-driven centrifugal pump.

State vector ``x = [omega, T_m, T_f, p_s]``:

    omega   shaft angular speed                      [rad/s]
    T_m     motor winding/body temperature           [degC]
    T_f     process-side (fluid) temperature         [degC]
    p_s     smoothed discharge gauge pressure        [Pa]

Equations (documented in docs/MATHEMATICAL_MODEL.md; u = load demand in [0,1]):

    J d(omega)/dt  = tau_m(u, omega) - tau_p(omega, d_imp) - tau_fric(omega, d_b)
    C_m dT_m/dt    = (1 - eta_m) * P_el - hA_m*(1 - k_oh*d_oh) * (T_m - T_amb)
    C_f dT_f/dt    = k_gen + rho*c_p*Q_out*(T_in - T_f) + hA_f*(T_amb - T_f)
    tau_p d(p_s)/dt = p_target(omega, d_imp, d_blk) - p_s

Degradation faults enter as dimensionless progression factors d_i in [0,1]:
    d_b  bearing wear     d_oh  overheat          d_leak internal leakage
    d_imp impeller wear   d_blk partial blockage

The model is intentionally first-principles-shaped but *lumped*: affinity
laws for the pump, slip-line torque for the motor, first-order thermal
lumps. It is a research-grade simulator calibrated to a plausible generic
pump set, NOT a claim about any real SOMIZ machine.
"""

from __future__ import annotations

import numpy as np
from .config import MachineParams

# failure-mode keys used by the RHS (must match faults.py FAULT_TYPES)
D_BEARING = "bearing"
D_OVERHEAT = "overheating"
D_LEAK = "leakage"
D_IMP = "impeller"
D_BLOCK = "blockage"


class ZeroStateError(ValueError):
    pass


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------


class RotatingMachine:
    """State-space model with RK4 integration and algebraic sensor outputs."""

    def __init__(self, params: MachineParams):
        errs = params.validate()
        if errs:
            raise ValueError("invalid MachineParams: " + "; ".join(errs))
        self.p = params
        self.tau_max = params.tau_ref * params.tau_max_ratio
        self.eps_w = 1e-3  # speed below which pump torque is considered zero

    # -- physical helpers ---------------------------------------------------
    def motor_torque(self, u: float, omega: float) -> float:
        """Induction-motor torque on the linear slip-line.

        Torque falls linearly from breakdown at standstill to zero at sync
        speed; u scales demand (startup/load control).
        """
        p = self.p
        slip_ratio = (p.omega_sync - omega) / (p.omega_sync - p.omega_ref)
        return float(np.clip(u * p.tau_ref * slip_ratio, 0.0, self.tau_max))

    def pump_torque(self, omega: float, d_imp: float) -> float:
        """Hydraulic load torque from affinity-law head/flow.

        Rated hydraulic power P_h = rho*g*Q_ref*H_ref is scaled with speed
        squared (affinity) and degraded by impeller wear.
        """
        p = self.p
        if omega <= self.eps_w:
            return 0.0
        wn = omega / p.omega_ref
        q_p = p.Q_ref * wn * (1.0 - p.k_imp * d_imp)
        h_tot = p.H_ref * wn * wn * (1.0 - p.k_imp * d_imp)
        p_h = p.rho * 9.81 * q_p * h_tot
        tau = p_h / omega
        if not np.isfinite(tau):
            return 0.0
        return tau

    def friction_torque(self, omega: float, d_b: float) -> float:
        p = self.p
        if omega <= 0.0:
            return 0.0
        return p.c_f * omega * (1.0 + p.k_f * d_b)

    def p_target(self, omega: float, d_imp: float, d_blk: float) -> float:
        """Discharge gauge pressure target (Pa).

        Pressure rises with head (speed^2 affinity, impeller degradation
        reduces it) and rises further when the discharge is partially
        blocked; leakage does not change head directly (it reduces flow).
        """
        p = self.p
        wn = max(omega, 0.0) / p.omega_ref
        h_tot = p.H_ref * wn * wn * (1.0 - p.k_imp * d_imp) * (1.0 + p.k_block_head * d_blk)
        return p.rho * 9.81 * h_tot + p.p_suction

    def flow_out(self, omega: float, d_imp: float, d_leak: float, d_blk: float) -> float:
        """Net flow delivered to the system (m^3/s).

        Pump flow follows affinity law and impeller wear, minus internal
        recirculation (seal/impeller leakage), and is reduced further by
        partial discharge blockage.
        """
        p = self.p
        wn = max(omega, 0.0) / p.omega_ref
        q_p = p.Q_ref * wn * (1.0 - p.k_imp * d_imp)
        q_leak = p.k_leak * p.Q_ref * wn * d_leak
        q_out = max(0.0, q_p - q_leak) * (1.0 - p.k_block_flow * d_blk)
        return float(q_out)

    # -- RHS -----------------------------------------------------------------
    def rhs(self, x: np.ndarray, u: float, d: dict) -> np.ndarray:
        """Evaluate dx/dt at state x, load demand u and degradation dict d."""
        p = self.p
        omega, t_m, t_f, p_s = x
        if omega < 0.0:
            omega = 0.0

        d_b = d.get(D_BEARING, 0.0)
        d_oh = d.get(D_OVERHEAT, 0.0)
        d_imp = d.get(D_IMP, 0.0)
        d_leak = d.get(D_LEAK, 0.0)
        d_blk = d.get(D_BLOCK, 0.0)

        tau_m = self.motor_torque(u, omega)
        tau_p = self.pump_torque(omega, d_imp)
        tau_f = self.friction_torque(omega, d_b)
        d_omega = (tau_m - tau_p - tau_f) / p.J

        # electrical power and losses (motor braking: P_el >= 0)
        p_el = tau_m * omega / p.eta_motor if tau_m > 0.0 else 0.0
        p_loss = (1.0 - p.eta_motor) * p_el
        cooling = p.hA_m * (1.0 - p.k_overheat * d_oh) if d_oh <= 1.0 else p.hA_m * (1.0 - p.k_overheat)
        d_tm = (p_loss - cooling * (t_m - p.T_amb)) / p.C_m

        q_out = self.flow_out(omega, d_imp, d_leak, d_blk)
        d_tf = (p.k_gen + p.rho * p.c_p * q_out * (p.T_in - t_f) + p.hA_f * (p.T_amb - t_f)) / p.C_f

        p_t = self.p_target(omega, d_imp, d_blk)
        d_ps = (p_t - p_s) / p.tau_p

        return np.array([d_omega, d_tm, d_tf, d_ps], dtype=float)

    # -- integration ---------------------------------------------------------
    def x0(self) -> np.ndarray:
        p = self.p
        return np.array([0.0, p.T_init, p.T_init, p.p_suction], dtype=float)

    def step_rk4(self, x: np.ndarray, u: float, d: dict, dt: float) -> np.ndarray:
        k1 = self.rhs(x, u, d)
        k2 = self.rhs(x + 0.5 * dt * k1, u, d)
        k3 = self.rhs(x + 0.5 * dt * k2, u, d)
        k4 = self.rhs(x + dt * k3, u, d)
        return x + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)

    # -- algebraic outputs (used by the sensor layer) ------------------------
    def outputs(self, x: np.ndarray, u: float, d: dict) -> dict:
        """Physical outputs in raw SI/lab units used by SensorModel."""
        p = self.p
        omega, t_m, t_f, p_s = x
        d_b = d.get(D_BEARING, 0.0)
        d_imp = d.get(D_IMP, 0.0)
        d_leak = d.get(D_LEAK, 0.0)
        d_blk = d.get(D_BLOCK, 0.0)

        tau_m = self.motor_torque(u, omega)
        tau_p = self.pump_torque(omega, d_imp)
        p_el = tau_m * omega / p.eta_motor if tau_m > 0.0 else 0.0
        p_h = tau_p * omega if tau_p > 0.0 else 0.0
        q_out = self.flow_out(omega, d_imp, d_leak, d_blk)

        wn = max(omega, 0.0) / p.omega_ref
        vib = (p.vib_base + p.vib_bearing * d_b + p.vib_blockage * d_blk
               + p.vib_wear * max(d.values(), default=0.0)) * wn * wn
        p_target = self.p_target(omega, d_imp, d_blk)

        return {
            "omega_rad": float(omega),
            "speed_rpm": float(omega * 30.0 / np.pi),
            "motor_temp": float(t_m),
            "fluid_temp": float(t_f),
            "discharge_pressure_pa": float(p_s),
            "discharge_pressure_bar": float(p_s / 1e5),
            "p_target_pa": float(p_target),
            "flow_m3s": float(q_out),
            "flow_m3h": float(q_out * 3600.0),
            "motor_torque_nm": float(tau_m),
            "power_kw": float(p_el / 1000.0),
            "hydraulic_power_kw": float(p_h / 1000.0),
            "motor_current_a": float(p_el / (np.sqrt(3.0) * p.V_ll * p.cos_phi)) if p_el > 0 else 0.0,
            "efficiency": float((p_h / p_el) * 100.0) if p_el > 10.0 else 0.0,
            "vibration_rms": float(vib),
            "load_demand": float(u),
        }


def machine_outputs(x, u: float, d: dict, params: MachineParams) -> dict:
    """Stateless convenience wrapper (kept for API ergonomics)."""
    return RotatingMachine(params).outputs(x, u, d)