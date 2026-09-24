# Mathematical Model — Industrial Equipment Digital Twin

**Status:** SIMULATED MODEL (research-grade demonstrator)
**Model version:** `rotating-machine-lumped-v1` (see `simulation/physics.py`)

This document specifies the differential-algebraic model that drives the
synthetic sensor behaviour in the simulation. It is written to be auditable:
every equation below has a direct counterpart in code, and every simplifying
assumption is stated. **This file does not describe any real SOMIZ machine**;
the parameters are a generic, physically-plausible small industrial pump set
that can later be replaced with real company data without touching the code.

---

## 1. Scope and system

The flagship asset is a **motor-driven centrifugal pump**: an induction motor
coupled by a shaft to a single-stage centrifugal pump discharging into a
process line. This archetype covers the classic predictive-maintenance
failure mechanisms (bearing wear, overheating, seal leakage, impeller
erosion, partial blockage) and produces observable signals that share the
sensor set required by the platform (vibration, temperature, pressure, flow,
speed, current, power, efficiency).

## 2. State vector

```
x = [omega, T_m, T_f, p_s]^T
```

| Symbol | Meaning | Unit |
|---|---|---|
| `omega` | shaft angular speed | rad/s |
| `T_m` | motor winding/body temperature | °C |
| `T_f` | process-side (fluid) temperature | °C |
| `p_s` | smoothed discharge gauge pressure | Pa |

The control input is the load demand `u(t) ∈ [0, 1]` (piecewise-constant
operating profile; see `simulation/regimes.py`). The physical parameters
`theta` are collected in `simulation/config.py::MachineParams`.

## 3. Degradation states (fault progressions)

Physics faults enter as dimensionless progression factors `d_i(t) ∈ [0, 1]`:

| `d_i` | Failure mode | Primary physical effect |
|---|---|---|
| `d_b` | bearing wear | friction ↑, vibration ↑ |
| `d_oh` | overheating | motor cooling ↓ |
| `d_leak` | internal leakage (seal/impeller) | net flow ↓ |
| `d_imp` | impeller erosion | flow & head ↓ |
| `d_blk` | partial blockage | flow ↓, pressure & vibration ↑ |

Each `d_i` is generated from a configurable fault spec (onset time, target
severity, duration, shape `linear | exponential | step`) — see
`simulation/faults.py`. They are **not** part of the ODE state: their
evolution is prescribed, which keeps the physics observable and the
ground-truth label (health stage) exact. A global health stage
`NORMAL → EARLY → MODERATE → SEVERE → FAILURE` is derived from the worst
progression via configurable thresholds (default 0.05/0.30/0.60/0.90).

## 4. Differential equations

### 4.1 Rotor dynamics

```
J · d(omega)/dt = tau_m(u, omega) − tau_p(omega, d_imp) − tau_fric(omega, d_b)
```

- **Motor torque** (induction motor, linear slip-line):

```
tau_m(u, omega) = clamp( u · tau_ref · (omega_sync − omega) / (omega_sync − omega_ref),
                         0,  tau_max )
tau_max = tau_max_ratio · tau_ref
```

The slip ratio equals 1 at rated speed (so `tau_m = u·tau_ref` there) and 0
at synchronous speed; this gives the realistic soft start-up and the
speed-droop under load.

- **Pump hydraulic torque** (centrifugal affinity laws): with `wn = omega/omega_ref`,

```
Q_p   = Q_ref · wn · (1 − k_imp · d_imp)          pump-generated flow
h_tot = H_ref · wn² · (1 − k_imp · d_imp)         pump total head
P_h   = rho · g · Q_p · h_tot                     hydraulic power
tau_p = P_h / omega                               (0 if omega ≈ 0)
```

Affinity laws (Q ∝ ω, H ∝ ω², P_h ∝ ω³) are the classic centrifugal-pump
approximation and are the source of the speed²/³ scalings verified in tests.

- **Friction torque** (wear-dependent):

```
tau_fric(omega, d_b) = c_f · omega · (1 + k_f · d_b)
```

### 4.2 Motor thermal balance

```
C_m · dT_m/dt = (1 − eta_m) · P_el − hA_m · (1 − k_overheat · d_oh) · (T_m − T_amb)
P_el = tau_m · omega / eta_m
```

Electrical power in exceeds mechanical out by the motor losses; the excess
warms the lumped motor mass, balanced by convection to ambient. The
overheating fault reduces the convection coefficient (blocked cooling path).

### 4.3 Fluid / process thermal balance

```
C_f · dT_f/dt = k_gen + rho · c_p · Q_out · (T_in − T_f) + hA_f · (T_amb − T_f)
```

`Q_out` is the net delivered flow (below): pumping drives the process
temperature toward inlet temperature; parasitic heat and ambient exchange
complete the balance.

### 4.4 Discharge pressure dynamics (first-order smoothing)

The true discharge pressure responds fast (line dynamics); we model a
first-order lag with time constant `tau_p` so the observation has plausible
inertia:

```
tau_p · d(p_s)/dt = p_target(omega, d_imp, d_blk) − p_s
p_target = rho · g · H_ref · wn² · (1 − k_imp·d_imp) · (1 + k_block_head·d_blk) + p_suction
```

### 4.5 Net delivered flow (algebraic)

```
Q_p    = Q_ref · wn · (1 − k_imp · d_imp)
Q_leak = k_leak · Q_ref · wn · d_leak
Q_out  = max(0, Q_p − Q_leak) · (1 − k_block_flow · d_blk)
```

**Documented model assumptions:**
- Leakage reduces *flow*; it does not directly raise head (handled via
  blockage instead). This mirrors an internal recirculation path.
- Blockage reduces delivered flow *and* raises discharge pressure (increased
  resistance) and vibration.
- No static head offset is modelled (`p_suction` is configurable; a future
  extension may add `H_st` for the static component).

## 5. Observation model

### 5.1 Physical outputs (raw)

```
speed      omega_rpm = omega · 30 / pi
flow       Q_out · 3600                      [m³/h]
pressure   p_s / 1e5                         [bar]
current    I = P_el / (sqrt(3) · V_ll · cos_phi)     [A]
power      P_el / 1000                       [kW]
efficiency eta = 100 · P_h / P_el            [%]  (0 when P_el ≤ 10 W)
vibration  v = (v_base + v_bearing·d_b + v_blockage·d_blk + v_wear·d_max) · wn²   [mm/s RMS]
```

The vibration law captures the two classic signatures: amplitude grows with
bearing wear and blockage, and scales with speed squared (a steadily
rotating machine vibrates more than a slow one; at rest it is quiet).

### 5.2 Instrument model

Each observed channel follows

```
y(t) = h(x(t), u(t), theta) + eps(t) + drift + anomalies + missing/outliers
```

with seeded Gaussian noise (absolute and/or relative), optional linear
drift, time-windowed sensor anomalies (`drift`, `stuck`, `noise_burst`,
`outlier_burst`), missing samples (NaN with probability p), and outlier
spikes (±5–10σ with probability p). Full details: `simulation/sensors.py`.

## 6. Numerical integration

- Fixed-step classical **RK4** with `dt_phys` = 0.25 s default (configurable;
  stiff to none of these mild equations at this scale).
- Sampling at `fs_hz` (default 1 Hz); physics is advanced between sample
  instants in `dt_phys` sub-steps.
- Deterministic: every stochastic draw comes from `np.random.default_rng(seed)`;
  the same `SimulationConfig` reproduces the same data frame bit-for-bit.

## 7. Failure-mode catalogue (reference)

| Fault type | `d_i` | Onset/target/duration | Symptom |
|---|---|---|---|
| bearing | `d_b` | configurable | friction ↑, speed droop, vibration ↑↑ |
| overheating | `d_oh` | configurable | motor temp ↑↑, current slight ↑ |
| leakage | `d_leak` | configurable | net flow ↓, (head unchanged) |
| impeller | `d_imp` | configurable | flow ↓ and head ↓ |
| blockage | `d_blk` | configurable | flow ↓, pressure ↑, vibration ↑ |

**Simulation-time caveat:** degradation is accelerated relative to real
lifetime (hours instead of months) so the full NORMAL→FAILURE trajectory is
visible in a demo. This is a stated modelling assumption, not a calibrated
life model; RUL derived from it is a *simulation performance* metric, not a
real-world prediction.

## 8. Validation status

Automated checks in `tests/test_physics.py` verify for every commit:
- parameter sanity (invalid `J`, `eta`, speeds, breakdown torque, etc. rejected);
- torque model at rated speed, sync speed, standstill and clipping;
- affinity scalings (pump torque ∝ ω²);
- friction growth with bearing wear;
- all fault→physics couplings (impeller ↓ flow, leakage ↓ flow, blockage
  ↓ flow & ↑ pressure, overheat ↑ temperature, bearing ↑ vibration & ↓ speed);
- numerical stability over long runs (no NaN) and finite, non-negative,
  physically plausible outputs at rest, running and degraded states.