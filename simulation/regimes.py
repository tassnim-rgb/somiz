"""Operating regime generator: a piecewise-constant load profile u(t) in [0,1].

Startup/shutdown transients emerge from the torque dynamics in
``physics.RotatingMachine`` (motor torque ramp vs load torque); the profile
only drives the demand. The default profile exercises startup, steady load,
a load step, shutdown, an off period and a restart.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from .config import OperatingProfileSpec


@dataclass
class OperatingProfile:
    """Sorted segments [(t_end, u), ...] with optional cycling."""

    segments: List[Tuple[float, float]]
    cycle: bool = False

    def __post_init__(self):
        ends = [e for e, _ in self.segments]
        if any(e <= 0 for e in ends):
            raise ValueError("segment ends must be positive and increasing")
        if any(a >= b for a, b in zip(ends, ends[1:])):
            raise ValueError("segments must be sorted with increasing end times")
        for _e, u in self.segments:
            if not 0.0 <= u <= 1.0:
                raise ValueError("load demand u must be in [0, 1]")

    def u_at(self, t: float) -> float:
        if not self.segments:
            return 0.0
        if self.cycle:
            period = self.segments[-1][0]
            t = t % period
        last_u = self.segments[0][1]
        for end, u in self.segments:
            if t < end:
                return last_u
            last_u = u
        return last_u  # after last segment: hold last value

    def as_pairs(self) -> List[Tuple[float, float]]:
        return [(e, u) for e, u in self.segments]


def profile_from_spec(spec: OperatingProfileSpec) -> OperatingProfile:
    return OperatingProfile(
        segments=[(float(e), float(u)) for e, u in spec.segments],
        cycle=spec.cycle,
    )