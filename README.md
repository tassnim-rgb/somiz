# SOMIZ — Digital Shadow (Maintenance Intelligente)

A single-file, browser-based **digital shadow** of an industrial plant
(modeled on the SOMIZ site, Arzew — Oran, Algeria): 4 ateliers, 69 machines,
each with a live sensor panel and a 3D floor plan.

> ⚠️ **HONEST SCOPE — the data is SIMULATED.**
> There is **no live sensor connection yet** (no PLC/SCADA/TIWEST feed). The
> top bar displays `FLUX SIMULÉ ACTIF` to make that explicit. The simulation
> is designed to be swapped for real telemetry without touching the UI — see
> [Connecting real data](#connecting-real-data).

## What it does

- **3D ateliers** (DIS, DLOG, Centrale, DCA) with zones, per-machine geometry
  per archetype (tour, fraiseuse, scie, presse, compresseur, four, perceuse,
  ventilateur, générique), raycaster selection, tooltips, orbit/zoom.
- **Live sensor panel** per machine: 3 channels (vibration/temp/rpm — or
  pressure/speed/load depending on archetype) with plausibly *correlated*
  behavior (see [Simulation model](#simulation-model)).
- **Health engine**: each machine has a hidden *wear* state that drifts
  upward with age/criticality, suffers rare fault shocks, and is periodically
  restored by corrective maintenance. Status (Ok → À surveiller → Dégradé →
  Critique) is *derived* from wear, so changes are gradual and believable.
- **Event feed**: status changes, maintenance actions, and sensor exceedance
  micro-events are timestamped and logged.
- **Animated machines**: chucks, workpieces, spindles, saw blades, press rams,
  drill bits, fans and heat glows move at speed/roughness set by health —
  healthy = smooth, worn = stuttering, critical = nearly seized.

## Simulation model

Sensors follow a small process model instead of a random walk:

```
value = mean(wear) × (1 + AR(1) noise) × (1 + rotary periodic)
```

- `mean` creeps toward a target scaled by health
  (`SENSOR_SCALE`: ok 1.0 → critical 1.95) — the classic early-warning
  signature of wear.
- The AR(1) colored-noise term makes readings wander smoothly, not jump.
- The rotary term (sinusoid) grows with wear, modeling bearing imbalance.
- Sensor values in the panel update every 2 s; status (health) ticks every 6 s;
  machine motion animates per frame at 60 fps.

Machine motion is driven by a per-status profile
`{ ok, warn, danger, critical } → { speed, roughness, glow }`:

| Status | Speed | Roughness | Glow |
|---|---|---|---|
| ok | 100% | low | subtle |
| warn | 85% | a little | moderate |
| danger | 65% | strong | strong |
| critical | 10% | violent stutter | intense |

## Running

No build step, no dependencies beyond a browser:

```bash
python3 -m http.server 8000 --directory .
# open http://localhost:8000
```

(The page loads Three.js r128 from cdnjs and IBM Plex fonts from Google
Fonts; an internet connection is required for first load.)

Controls: left-drag orbit · scroll zoom · click a machine for its panel.

## Connecting real data

The simulation is intentionally centralized so it can be replaced by a
telemetry bridge:

1. `genSensors(mtype, status)` defines each machine's channels and their
   nominal (`base`) values — map these to real tag addresses
   (e.g. `DIS-02/Vib/4-20mA`).
2. `tickSensors()` is the only writer of `eq.sensors[i].value`. Replace its
   body with a poll of your historian/broker (OPC UA / Modbus / MQTT) and the
   whole UI updates unchanged.
3. `tickHealth()` (status derivation) can be driven by real alarms/key
   performance indicators instead of the wear model.

## Files

| File | Contents |
|---|---|
| `index.html` | entire application (HTML + CSS + Three.js scene + simulation) |

## A note on names

SOMIZ is the real industrial site name; plant layout, equipment names and
maintenance records in this demo are **illustrative placeholders**, not
exported plant data.