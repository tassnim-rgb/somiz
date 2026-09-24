"""Feature engineering: trailing rolling statistics, rate-of-change, and
frequency-domain features.

Rolling features use pandas trailing windows (``closed='left'`` behaviour via
shift) so each row only sees past samples — no future leakage by
construction.

Spectral features are computed per *window* (slice) after the chronological
split; each window belongs entirely to one fold (leakage-safe by design).
"""

from __future__ import annotations

from typing import Iterable, List

import numpy as np
import pandas as pd

ROLL_STATS = ("mean", "std", "min", "max", "median")


def rolling_features(
    df: pd.DataFrame,
    columns: Iterable[str],
    window: int = 60,
    stats: Iterable[str] = ROLL_STATS,
    shift: int = 1,
) -> pd.DataFrame:
    """Add trailing rolling statistics for ``columns``.

    ``shift`` (default 1) excludes the current row from the window so a
    feature at time t cannot include the very value at t (a pure
    causal/one-step-lag feature).
    """
    if window < 2:
        raise ValueError("window must be >= 2")
    out = df.copy()
    cols = [c for c in columns if c in out.columns]
    for c in cols:
        s = out[c].shift(shift)
        for stat in stats:
            out[f"{c}_roll{window}_{stat}"] = getattr(s.rolling(window, min_periods=1), stat)()
    return out


def rate_of_change(
    df: pd.DataFrame,
    columns: Iterable[str],
) -> pd.DataFrame:
    """Add per-column first differences (delta and absolute delta)."""
    out = df.copy()
    for c in [c for c in columns if c in out.columns]:
        d = out[c].diff()
        out[f"{c}_delta"] = d
        out[f"{c}_delta_abs"] = d.abs()
    return out


def spectral_features_frame(
    df: pd.DataFrame,
    columns: Iterable[str],
    fs_hz: float,
    window: int = 512,
    stride: int = 256,
) -> pd.DataFrame:
    """Frequency-domain features per contiguous window.

    Returns a DataFrame with one row per window:
    ``window_start`` (sample index), ``t_start`` (seconds, if 't' present),
    and per column: dominant frequency (Hz), spectral centroid (Hz),
    and the low-band energy ratio (0-25% of Nyquist).

    Intended to be computed *after* chronological splitting so windows never
    straddle folds; call it separately on each split.
    """
    if window < 8 or stride < 1:
        raise ValueError("window >= 8 and stride >= 1 required")
    cols = [c for c in columns if c in df.columns]
    if not cols:
        raise ValueError("no valid columns")
    n = len(df)
    t_arr = df["t"].to_numpy() if "t" in df.columns else None
    rows = []
    freqs = np.fft.rfftfreq(window, d=1.0 / fs_hz)
    low_band = freqs <= 0.25 * (fs_hz / 2.0)
    for start in range(0, n - window + 1, stride):
        rec = {"window_start": start}
        if t_arr is not None:
            rec["t_start"] = float(t_arr[start])
        for c in cols:
            seg = df[c].to_numpy()[start:start + window]
            # NaN-safe: impute internal NaNs with linear interpolation of the window
            if np.isnan(seg).any():
                idx = np.arange(window)
                good = ~np.isnan(seg)
                if good.sum() == 0:
                    seg = np.zeros(window)
                else:
                    seg = np.interp(idx, idx[good], seg[good])
            sp = np.abs(np.fft.rfft(seg))
            total = sp.sum()
            if total <= 0:
                dom = cen = 0.0
                low_ratio = 0.0
            else:
                dom = float(freqs[np.argmax(sp)])
                cen = float((freqs * sp).sum() / total)
                low_ratio = float(sp[low_band].sum() / total)
            rec[f"{c}_spec_dom_hz"] = dom
            rec[f"{c}_spec_centroid_hz"] = cen
            rec[f"{c}_spec_low_ratio"] = low_ratio
        rows.append(rec)
    if not rows:
        raise ValueError(f"series too short for window={window}")
    return pd.DataFrame(rows)