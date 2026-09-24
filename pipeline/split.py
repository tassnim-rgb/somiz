"""Chronological (non-shuffled) train/validation/test splitting.

Leakage policy (documented and enforced here):
  - splits are always contiguous in time and never shuffled;
  - statistics for normalisation/features are fit on TRAIN only;
  - rolling features use trailing windows only (each value depends on past
    samples, never the future);
  - spectral features are computed per window AFTER the split, so each
    window belongs entirely to one fold.
"""

from __future__ import annotations

from typing import Generator, Tuple

import pandas as pd


def chrono_split(
    df: pd.DataFrame,
    fit_frac: float = 0.6,
    val_frac: float = 0.2,
    t_col: str = "t",
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split a time series into contiguous (fit, validation, test) slices.

    Raises ValueError if fractions are invalid or the index is not monotonic
    increasing in time.
    """
    if not 0.0 < fit_frac < 1.0 or not 0.0 <= val_frac < 1.0 - fit_frac:
        raise ValueError("require 0 < fit_frac < 1 and 0 <= val_frac < 1 - fit_frac")
    t = df[t_col].to_numpy()
    if (t[1:] < t[:-1]).any():
        raise ValueError("time column must be monotonically non-decreasing")
    if (t[1:] == t[:-1]).any():
        raise ValueError("time column contains duplicate timestamps (expected unique per row)")

    n = len(df)
    i_fit = int(round(n * fit_frac))
    i_val = int(round(n * (fit_frac + val_frac)))
    fit = df.iloc[:i_fit].reset_index(drop=True)
    val = df.iloc[i_fit:i_val].reset_index(drop=True)
    test = df.iloc[i_val:].reset_index(drop=True)
    if len(test) == 0:
        raise ValueError("test slice is empty; reduce fit/val fractions")
    return fit, val, test


def expanding_window_cv(
    df: pd.DataFrame,
    n_folds: int = 3,
    min_fit: int = 1000,
    horizon: int = 0,
) -> Generator[Tuple[pd.DataFrame, pd.DataFrame], None, None]:
    """Expanding-window time-series cross validation.

    For each fold the training set grows (expanding) and the validation set
    is the following block. ``horizon`` is a purging gap (in rows) between
    train and validation to avoid label leakage across the boundary — a
    standard safeguard for models that use context windows.
    """
    if n_folds < 2:
        raise ValueError("n_folds must be >= 2")
    n = len(df)
    if min_fit + horizon >= n:
        raise ValueError("min_fit + horizon exceeds data length")
    step = (n - min_fit - horizon) // n_folds
    if step < 1:
        raise ValueError("not enough data for the requested folds")
    start = 0
    while start + min_fit + horizon + step <= n and start + min_fit + step < n:
        end = start + min_fit
        if end + horizon >= n:
            return
        first_val = end + horizon
        last_val = min(n, first_val + step)
        if last_val - first_val < 1:
            return
        yield df.iloc[start:end].reset_index(drop=True), \
            df.iloc[first_val:last_val].reset_index(drop=True)
        start = end