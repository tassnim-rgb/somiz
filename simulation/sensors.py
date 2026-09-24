"""Sensor model: turns raw physical outputs into plausible instrument
readings in display units.

Supported imperfections (all configurable, all seeded for reproducibility):
  - Gaussian noise (absolute and/or relative)
  - linear drift
  - missing samples (NaN) with probability p
  - outlier spikes with probability p
  - time-windowed anomalies: drift / noise burst / outlier burst
    (stateless) and 'stuck' (stateful, handled by the Simulator via
    StuckHolder because it must hold the value captured at onset)
"""

from __future__ import annotations

import numpy as np
from typing import Dict, List

from .config import SensorAnomaly, SensorConfig


class SensorModel:
    """Applies imperfections to raw physical outputs.

    ``raw`` values are expected in display units (the physics layer emits
    both SI and display-unit keys); noise, drift, missing and outliers act
    on the display value.
    """

    def __init__(self, sensors: List[SensorConfig], anomalies: List[SensorAnomaly],
                 seed: int = 42):
        if not sensors:
            raise ValueError("need at least one sensor")
        self.sensors = list(sensors)
        self.anomalies = list(anomalies)
        self.by_tag = {s.tag: s for s in sensors}
        self.rng = np.random.default_rng(seed)

    def corrupt(self, raw: Dict[str, float], t: float) -> Dict[str, float]:
        """Return a dict tag -> corrupted display value (float or np.nan).

        Note: 'stuck' anomalies are NOT applied here (stateful); see
        ``apply_stuck`` and the Simulator.
        """
        out: Dict[str, float] = {}
        for s in self.sensors:
            value = raw.get(s.source, float("nan"))
            out[s.tag] = self._apply(s, value, t)
        return out

    def _apply(self, s: SensorConfig, value: float, t: float) -> float:
        if not np.isfinite(value):
            return float("nan")

        # 1) additive Gaussian noise (absolute + relative)
        if s.noise_std > 0:
            value += self.rng.normal(0.0, s.noise_std)
        if s.noise_rel > 0 and value != 0:
            value += value * self.rng.normal(0.0, s.noise_rel)

        # 2) linear drift
        if s.drift_rate != 0:
            value += s.drift_rate * t

        # 3) stateless time-windowed anomaly
        anom = self._active_anomaly(s.tag, t)
        if anom is not None:
            value = self._anomalize(s, value, anom, t)

        # 4) missing sample (NaN)
        if s.missing_p > 0 and self.rng.random() < s.missing_p:
            return float("nan")

        # 5) outlier spike: +/- outlier_sigma * (noise or 5% of value)
        if s.outlier_p > 0 and self.rng.random() < s.outlier_p:
            base = s.noise_std if s.noise_std > 0 else (0.05 * abs(value) if value else 1.0)
            value += self.rng.choice([-1.0, 1.0]) * s.outlier_sigma * base

        # clamp to plausible range
        value = min(max(value, s.lower), s.upper)
        return float(value)

    def _active_anomaly(self, tag: str, t: float):
        for a in self.anomalies:
            if a.sensor_tag == tag and a.onset_s <= t < a.onset_s + a.duration_s:
                return a
        return None

    def _anomalize(self, s: SensorConfig, value: float, a: SensorAnomaly, t: float) -> float:
        if a.kind == "drift":
            frac = (t - a.onset_s) / max(a.duration_s, 1e-6)
            return value * (1.0 + a.magnitude * 0.20 * frac)
        if a.kind == "noise_burst":
            sigma = a.magnitude * (s.noise_std if s.noise_std > 0 else 0.05 * abs(value))
            return value + self.rng.normal(0.0, sigma)
        if a.kind == "outlier_burst":
            return value + self.rng.choice([-1.0, 1.0]) * a.magnitude * (0.5 * abs(value) + 1e-9)
        return value

    # -- stateful 'stuck' support -------------------------------------------
    def stuck_holders(self) -> Dict[str, "StuckHolder"]:
        stuck = [a for a in self.anomalies if a.kind == "stuck"]
        holder: Dict[str, StuckHolder] = {}
        for a in stuck:
            if a.sensor_tag not in self.by_tag:
                raise ValueError(f"stuck anomaly references unknown sensor {a.sensor_tag!r}")
            holder.setdefault(a.sensor_tag, StuckHolder(self.by_tag[a.sensor_tag]))
        return holder


class StuckHolder:
    """Remembers the first value during a 'stuck' window (sensor freeze).

    The Simulator calls ``apply`` each sample with the corrupted (but not yet
    stuck) value; while inside the window the captured value is returned.
    """

    def __init__(self, cfg: SensorConfig):
        self.cfg = cfg
        self._captured: float | None = None

    def reset(self):
        self._captured = None

    def apply(self, value: float, t: float, a: SensorAnomaly) -> float:
        if t < a.onset_s:
            return value
        if t < a.onset_s + a.duration_s:
            if self._captured is None:
                self._captured = value
            return self._captured
        return value


def sensor_from_config(cfg: SensorConfig) -> SensorConfig:
    return cfg