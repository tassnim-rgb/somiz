"""Explainable machine health index (0-100, higher = healthier).

Formula (see docs/HEALTH_INDEX.md for the full derivation):

  1. A *commissioning reference curve* ref_s(t) is fitted per sensor on an
     observed (label-free) healthy qualification run of the same machine
     type and load profile. It is a time-indexed smooth mean over the
     healthy pool, which captures normal dynamics such as the slow thermal
     soak after start-up — otherwise a warm healthy machine would be
     misread as degraded.
  2. Per-sample standardised deviation
        z_s(t) = (x_s(t) - ref_s(t)) / sigma_s
     where sigma_s is the residual std of the healthy pool around ref_s.
  3. Noise-damped deviation (trailing window mean) to avoid single-sample
     jitter driving the index.
  4. Composite deviation  D(t) = sqrt( sum_s w_s * z_s(t)^2 / sum_s w_s )
     over a small, documented set of health-relevant sensors.
  5. Health index  HI(t) = 100 * exp(-D(t) / tau).

The index is therefore a smooth monotonic map of *how far the machine is
living from its own healthy reference*. Which sensors contributed most can
be reported for explainability (top contributors by weighted |z|).

It is validated (not tuned) against the simulator ground truth in
scripts/run_anomaly_experiment.py; the 0-100 bands below are a-priori, not
fitted to the data.

Model assumptions (documented, not fabricated):
  - The reference extends to the end of the healthy fit window; beyond it
    the last reference value is extrapolated (machine assumed at steady
    state).
  - Samples with t < warmup_s are the start-up transient: the index is not
    defined there (stage WARMUP, HI = NaN).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

DEFAULT_SENSOR_WEIGHTS: Dict[str, float] = {
    "vib": 1.5,        # bearing signature
    "t_motor": 1.0,    # thermal anomaly
    "efficiency": 1.0, # energy conversion loss
    "current": 0.8,    # electrical strain
    "flow": 0.6,       # hydraulic performance
    "p_disch": 0.6,    # discharge performance
    "t_fluid": 0.4,
    "rpm": 0.4,
}

# a-priori bands on the 0-100 scale (higher = healthier)
DEFAULT_BANDS: List[Tuple[str, float, float]] = [
    ("NORMAL", 80.0, 100.0),
    ("EARLY", 60.0, 80.0),
    ("MODERATE", 40.0, 60.0),
    ("SEVERE", 20.0, 40.0),
    ("FAILURE", 0.0, 20.0),
]


@dataclass
class HealthIndexConfig:
    sensor_weights: Dict[str, float] = field(default_factory=lambda: dict(DEFAULT_SENSOR_WEIGHTS))
    window: int = 60              # trailing smoothing window for z-scores
    tau: float = 2.0              # HI = 100*exp(-D/tau)
    warmup_s: float = 120.0       # start-up transient: index not defined before this
    ref_smooth_s: float = 300.0   # smoothing of the commissioning reference curve
    bands: List[Tuple[str, float, float]] = field(default_factory=lambda: list(DEFAULT_BANDS))

    def validate(self) -> List[str]:
        errs = []
        if self.window < 1:
            errs.append("window must be >= 1")
        if not self.tau > 0:
            errs.append("tau must be > 0")
        if self.warmup_s < 0:
            errs.append("warmup_s must be >= 0")
        if self.ref_smooth_s < 1:
            errs.append("ref_smooth_s must be >= 1")
        if not self.sensor_weights:
            errs.append("sensor_weights must not be empty")
        if any(w < 0 for w in self.sensor_weights.values()):
            errs.append("weights must be >= 0")
        lo_prev = None
        for name, lo, hi in self.bands:
            if hi <= lo:
                errs.append(f"band {name}: hi must be > lo")
            if lo_prev is not None and lo > lo_prev:
                errs.append(f"bands out of order (got {name} lo={lo} after lo={lo_prev})")
            lo_prev = lo
        # adjacent bands must tile the scale without gaps or overlaps
        for (n1, l1, h1), (n2, l2, h2) in zip(self.bands, self.bands[1:]):
            if l1 != h2:
                errs.append(f"gap or overlap between {n1} [{l1},{h1}] and {n2} [{l2},{h2}]")
        if len(self.bands) == 0:
            errs.append("at least one band required")
        return errs

    def band_of(self, hi: float) -> str:
        for name, lo, hi_b in self.bands:
            if lo <= hi <= hi_b:
                return name
        return self.bands[0][0] if hi > self.bands[0][1] else self.bands[-1][0]


@dataclass
class HealthIndexReport:
    """Per-asset summary of health-index behaviour vs ground truth."""

    asset_id: str
    hi_mean: float
    hi_min: float
    pearson_r_with_severity: float
    stage_alignment: float          # fraction of samples where band == ground-truth stage
    n_samples: int
    band_confusion: Dict[str, Dict[str, int]]


class HealthIndex:
    """Fit/evaluate health index from observed sensor data only."""

    def __init__(self, config: HealthIndexConfig | None = None):
        self.cfg = config or HealthIndexConfig()
        errs = self.cfg.validate()
        if errs:
            raise ValueError("invalid HealthIndexConfig: " + "; ".join(errs))
        self._ref: Dict[str, Tuple[np.ndarray, np.ndarray]] = {}  # sensor -> (t_grid, ref)
        self._sigma: Dict[str, float] = {}
        self.sensor_cols: List[str] = []

    # ------------------------------------------------------------------
    def fit(self, healthy_df: pd.DataFrame) -> "HealthIndex":
        """Fit the commissioning reference from an observed (label-free)
        healthy qualification run of the same machine type/load profile.

        Uses the steady-state portion (``t >= warmup_s``) of the healthy
        pool; the reference curve is a time-indexed smooth per-sensor mean,
        and ``sigma_s`` is the residual std of the pool around that curve.
        """
        if "t" not in healthy_df.columns:
            raise ValueError("healthy_df must contain a 't' (time) column")
        cols = [c for c in self.cfg.sensor_weights if c in healthy_df.columns]
        if not cols:
            raise ValueError("no weighted sensor columns present in fit frame")
        self.sensor_cols = cols

        df = healthy_df
        if self.cfg.warmup_s > 0:
            df = df[df["t"] >= self.cfg.warmup_s]
        if len(df) == 0:
            raise ValueError("no samples after warmup to build a reference")

        t = df["t"].to_numpy(dtype=float)
        for c in cols:
            x = df[c].to_numpy(dtype=float)
            # per-time mean over the healthy pool (assets share the t grid)
            g = df.groupby("t")[c].mean().sort_index()
            tg = g.index.to_numpy(dtype=float)
            ref = g.to_numpy(dtype=float)
            # smooth the commissioning signature (centered: it is a static
            # record of the qualification run, not a live signal)
            win = max(3, int(round(self.cfg.ref_smooth_s)))
            ref = pd.Series(ref).rolling(win, center=True,
                                          min_periods=1).mean().to_numpy()
            mu = np.interp(t, tg, ref, left=ref[0], right=ref[-1])
            resid = x - mu
            finite = np.isfinite(resid)
            if finite.sum() < 25:
                raise ValueError(
                    f"sensor {c!r}: too few finite residuals to estimate sigma")
            sigma = float(np.std(resid[finite]))
            if sigma < 1e-12:
                sigma = 1.0  # constant column: treat as uninformative (z=0)
            self._ref[c] = (tg, ref)
            self._sigma[c] = sigma
        return self

    def member_sensors(self) -> List[str]:
        return list(self.sensor_cols)

    # ------------------------------------------------------------------
    def evaluate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return a frame with ``hi`` (health index) and ``hi_stage`` columns
        plus per-sensor smoothed deviations ``wz_<sensor>`` and a per-sample
        top-3 contributor string ``top_signals`` (explainability).

        Samples with ``t < warmup_s`` get ``hi = NaN`` and stage ``WARMUP``:
        the index is not defined during the start-up transient. Singlesensor
        dropouts (NaN telemetry) leave ``hi = NaN`` and stage ``NO_READING``
        instead of fabricating a value.
        """
        if not self._ref:
            raise RuntimeError("evaluate() before fit()")
        if "t" not in df.columns:
            raise ValueError("df must contain a 't' (time) column")
        out = pd.DataFrame(index=df.index)
        t = df["t"].to_numpy(dtype=float)
        warmup_mask = t < self.cfg.warmup_s
        ws = np.array([self.cfg.sensor_weights[c] for c in self.sensor_cols])
        wsum = ws.sum()
        dev: Dict[str, np.ndarray] = {}
        for i, c in enumerate(self.sensor_cols):
            tg, ref = self._ref[c]
            mu = np.interp(t, tg, ref, left=ref[0], right=ref[-1])
            z = (df[c].to_numpy(dtype=float) - mu) / self._sigma[c]
            z = pd.Series(z).rolling(self.cfg.window, min_periods=1).mean().to_numpy()
            z = np.where(warmup_mask, np.nan, z)
            wz = z * ws[i]
            dev[c] = wz
            out[f"wz_{c}"] = z
        D = np.sqrt(np.sum(np.stack(list(dev.values())) ** 2, axis=0) / wsum)
        hi = 100.0 * np.exp(-D / self.cfg.tau)
        out["hi"] = hi
        # stage: WARMUP (start-up transient), NO_READING (sensor dropout: the
        # residual is undefined), otherwise the a-priori band of the index
        stages = []
        for h, wm in zip(hi, warmup_mask):
            if wm:
                stages.append("WARMUP")
            elif np.isfinite(h):
                stages.append(self.cfg.band_of(h))
            else:
                stages.append("NO_READING")
        out["hi_stage"] = stages

        # explainability: top-3 contributors by |weighted z| at each sample
        mat = np.stack(list(dev.values()), axis=1)  # (N, n_sensors)
        order = np.argsort(-np.abs(mat), axis=1)[:, :3]
        names = np.array(self.sensor_cols)
        out["top_signals"] = [
            "" if warmup_mask[i] else "+".join(names[row].tolist())
            for i, row in enumerate(order)
        ]
        return out

    # ------------------------------------------------------------------
    def validate(self, df: pd.DataFrame, severity_col: str = "fault_severity",
                 stage_col: str = "health_stage", asset_id: str = "?") -> HealthIndexReport:
        """Compare the explainable index against the simulator ground truth.

        Returns correlation with severity and band-vs-stage alignment (both
        computed on steady-state samples only). Used for evaluation only —
        never for tuning (avoiding label leakage).
        """
        ev = self.evaluate(df)
        steady = ev[ev["hi_stage"].isin(["WARMUP", "NO_READING"]) == False]
        sev = df.loc[steady.index, severity_col].to_numpy(dtype=float)
        r = float(np.corrcoef(ev.loc[steady.index, "hi"].to_numpy(), sev)[0, 1]) \
            if len(steady) > 1 and np.std(sev) > 1e-12 else float("nan")
        gt = df.loc[steady.index, stage_col].to_numpy()
        pred = steady["hi_stage"].to_numpy()
        align = float((pred == gt).mean())
        confusion: Dict[str, Dict[str, int]] = {}
        for a, b in zip(gt, pred):
            confusion.setdefault(str(a), {}).setdefault(str(b), 0)
            confusion[str(a)][str(b)] += 1
        return HealthIndexReport(
            asset_id=asset_id,
            hi_mean=float(ev.loc[steady.index, "hi"].mean()),
            hi_min=float(ev.loc[steady.index, "hi"].min()),
            pearson_r_with_severity=r,
            stage_alignment=align,
            n_samples=len(df),
            band_confusion=confusion,
        )