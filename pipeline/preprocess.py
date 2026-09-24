"""Preprocessing pipeline for time-series frames.

Order of operations (each step is logged in ``transform_log``; see
docs/DATA_GENERATION.md for the full policy):

  1. validate      : schema (required columns), monotonic time, plausible
                     ranges, NaN census
  2. impute        : fit-free interpolation (linear / ffill / none)
  3. split         : chronological (fit | validation | test), never shuffled
  4. fit scaler    : normalisation parameters computed on FIT slice only
  5. transform     : apply scaler to all slices
  6. features      : trailing rolling stats + rate of change (no future leak)
  7. spectral      : optional per-window FFT features (post-split, each
                     window within one fold)

Anti-leakage rules enforced by design:
  - scaler / constants fitted on fit-slice only;
  - rolling windows are trailing and shifted by one row;
  - spectral windows never straddle folds;
  - no global statistics computed over the whole series before splitting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from .features import rate_of_change, rolling_features
from .schema import REQUIRED_COLUMNS, RANGE_BOUNDS, SENSOR_COLUMNS, is_sensor
from .split import chrono_split


@dataclass
class ValidationReport:
    ok: bool
    issues: List[str]
    n_nan_by_column: dict
    n_rows: int
    t_min: float
    t_max: float

    def summary(self) -> str:
        head = "OK" if self.ok else "ISSUES"
        return f"[{head}] {len(self.issues)} issue(s), {self.n_rows} rows, t={self.t_min:.1f}..{self.t_max:.1f}s"


@dataclass
class PreprocessConfig:
    impute: str = "linear"            # none | linear | ffill
    normalize: str = "zscore"         # none | zscore | robust | minmax
    rolling_window: int = 60          # trailing rolling stats window (0 = off)
    rolling_stats: Tuple[str, ...] = ("mean", "std", "min", "max", "median")
    add_rate_of_change: bool = True
    drop_constant_cols: bool = True
    add_anomaly_target: bool = True   # binary: fault_severity >= early threshold
    anomaly_threshold: float = 0.05   # matches default EARLY stage onset
    robust_quantiles: Tuple[float, float] = (10.0, 90.0)


class Preprocessor:
    """Fit/transform preprocessor with a documented transform log."""

    def __init__(self, config: PreprocessConfig | None = None):
        self.cfg = config or PreprocessConfig()
        self.sensor_cols: List[str] = []
        self._scaler: Optional[dict] = None
        self._drop_cols: List[str] = []
        self.transform_log: List[str] = []
        self.latest_report: Optional[ValidationReport] = None

    # ------------------------------------------------------------------
    # Validation & imputation (fit-free)
    # ------------------------------------------------------------------
    def validate(self, df: pd.DataFrame) -> ValidationReport:
        issues: List[str] = []
        for col in REQUIRED_COLUMNS:
            if col not in df.columns:
                issues.append(f"missing required column {col!r}")
        if "t" in df.columns:
            t = df["t"].to_numpy()
            if (t[1:] < t[:-1]).any():
                issues.append("time column not monotonically increasing")
            if (t[1:] == t[:-1]).any():
                issues.append("duplicate timestamps")
        n_nan: dict = {}
        for c in df.columns:
            nn = int(df[c].isna().sum())
            if nn:
                n_nan[c] = nn
        for c in SENSOR_COLUMNS:
            if c not in df.columns:
                continue
            lo, hi = RANGE_BOUNDS.get(c, (-np.inf, np.inf))
            v = df[c]
            finite = v[np.isfinite(v)]
            if len(finite) and ((finite < lo).any() or (finite > hi).any()):
                issues.append(
                    f"sensor {c!r} out of plausible range [{lo}, {hi}]: "
                    f"actual [{finite.min():.3g}, {finite.max():.3g}]")
        self.sensor_cols = [c for c in SENSOR_COLUMNS if c in df.columns]
        report = ValidationReport(
            ok=not issues,
            issues=issues,
            n_nan_by_column=n_nan,
            n_rows=len(df),
            t_min=float(df["t"].min()) if "t" in df.columns else float("nan"),
            t_max=float(df["t"].max()) if "t" in df.columns else float("nan"),
        )
        self.latest_report = report
        return report

    def _impute(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        mode = self.cfg.impute
        if mode == "none":
            return out
        cols = [c for c in self.sensor_cols if c in out.columns]
        did = 0
        for c in cols:
            if not out[c].isna().any():
                continue
            did += 1
            if mode == "ffill":
                out[c] = out[c].ffill().bfill()
            elif mode == "linear":
                s = out[c]
                if s.notna().sum() == 0:
                    out[c] = pd.Series(0.0, index=s.index)
                else:
                    s = s.interpolate(method="linear", limit_direction="both")
                    out[c] = s
        if did:
            self.transform_log.append(f"impute: {mode} on {did} column(s)")
        return out

    # ------------------------------------------------------------------
    # Fit / transform
    # ------------------------------------------------------------------
    def fit(self, df: pd.DataFrame) -> "Preprocessor":
        report = self.validate(df)
        if not report.ok:
            raise ValueError("validation failed: " + "; ".join(report.issues))
        dfi = self._impute(df)
        if self.cfg.drop_constant_cols:
            const = [c for c in self.sensor_cols
                     if len(dfi[c].unique()) <= 1]
            self._drop_cols = const
        cols = [c for c in self.sensor_cols if c not in self._drop_cols]
        mode = self.cfg.normalize
        sc: dict = {}
        if mode == "zscore":
            for c in cols:
                # ddof=1 matches pandas Series.std() so fit-slice std == 1.0
                sc[c] = (float(dfi[c].mean()), float(dfi[c].std(ddof=1)))
        elif mode == "robust":
            for c in cols:
                lo, hi = np.nanpercentile(dfi[c], self.cfg.robust_quantiles)
                sc[c] = (float(np.nanmedian(dfi[c])), float(hi - lo))
        elif mode == "minmax":
            for c in cols:
                sc[c] = (float(dfi[c].min()), float(dfi[c].max()))
        self._scaler = sc or None
        self.transform_log.append(
            f"fit scaler '{mode}' on fit slice only -> columns {len(cols)}"
            + (f" (dropped constant: {self._drop_cols})" if self._drop_cols else ""))
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if self._scaler is None and self.cfg.normalize != "none":
            raise RuntimeError("transform() called before fit()")
        out = self._impute(df)
        if self._scaler:
            cols = [c for c in self.sensor_cols if c in self._scaler]
            if self.cfg.normalize == "zscore":
                for c in cols:
                    mu, sd = self._scaler[c]
                    out[c] = (out[c] - mu) / sd if sd > 0 else out[c] * 0.0
            elif self.cfg.normalize == "robust":
                for c in cols:
                    med, iq = self._scaler[c]
                    out[c] = (out[c] - med) / iq if iq > 0 else out[c] * 0.0
            elif self.cfg.normalize == "minmax":
                for c in cols:
                    mn, mx = self._scaler[c]
                    out[c] = (out[c] - mn) / (mx - mn) if mx > mn else out[c] * 0.0
            self.transform_log.append(f"apply scaler '{self.cfg.normalize}' on {len(cols)} columns")
        if self.cfg.rolling_window > 1:
            out = rolling_features(out, self.sensor_cols,
                                   window=self.cfg.rolling_window,
                                   stats=self.cfg.rolling_stats)
            self.transform_log.append(
                f"rolling features window={self.cfg.rolling_window} stats={list(self.cfg.rolling_stats)}")
        if self.cfg.add_rate_of_change:
            out = rate_of_change(out, self.sensor_cols)
            self.transform_log.append("rate-of-change (delta, delta_abs)")
        if self.cfg.add_anomaly_target and "fault_severity" in out.columns:
            out["anomaly_target"] = (out["fault_severity"] >= self.cfg.anomaly_threshold).astype(int)
            self.transform_log.append(
                f"anomaly target: fault_severity >= {self.cfg.anomaly_threshold}")
        return out

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.fit(df).transform(df)

    # ------------------------------------------------------------------
    # Convenience: validate -> impute -> chronological split -> fit on fit-slice
    # ------------------------------------------------------------------
    def split_transform(
        self, df: pd.DataFrame, fit_frac: float = 0.6, val_frac: float = 0.2
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Leakage-safe end-to-end path.

        Returns (fit, val, test) transformed; scaler fitted on fit-slice
        only; identical transforms applied to val/test.
        """
        report = self.validate(df)
        if not report.ok:
            raise ValueError("validation failed: " + "; ".join(report.issues))
        dfi = self._impute(df)
        fit, val, test = chrono_split(dfi, fit_frac, val_frac, t_col="t")
        self.fit(fit)
        return self.transform(fit), self.transform(val), self.transform(test)

    def report(self) -> str:
        lines = [f"Preprocessor ({self.cfg.normalize} / impute={self.cfg.impute})"]
        lines += [f"  - {m}" for m in self.transform_log]
        return "\n".join(lines)