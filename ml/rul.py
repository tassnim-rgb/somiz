"""Remaining Useful Life (RUL) prediction with uncertainty.

RUL is defined, per failure mode, as the time until the asset crosses its
*intervention threshold* (95 % of the scenario's target severity by default).
This is SIMULATED ground truth from the twin: degradation here is accelerated
(hours instead of months, see docs/MATHEMATICAL_MODEL.md) and deterministic
given the failure mode, so the RUL label is well defined. In a real
deployment the threshold and the label source come from the reliability
engineer; nothing here claims real-plant data.

Models:
  - Ridge: multivariate linear baseline.
  - GradientBoosting (mean): the classical tabular method.
  - Quantile GradientBoosting (p10 / p50 / p90): prediction intervals =
    a directly usable uncertainty estimate with a measurable coverage.
  - WindowMLPRegressor (PyTorch): temporal method on sliding windows of
    standardised sensors; predicts RUL from the recent degradation trend.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error

DEFAULT_CAP_S = 10800.0   # 3 h: any RUL above this is reported as the cap
THRESHOLD_FRAC = 0.95     # intervention threshold = 95 % of scenario target


# ---------------------------------------------------------------------------
# target construction
# ---------------------------------------------------------------------------


def build_rul_target(frame: pd.DataFrame, target: float,
                     threshold_frac: float = THRESHOLD_FRAC,
                     cap_s: float = DEFAULT_CAP_S) -> np.ndarray:
    """RUL(t) = max(0, t_fail - t), capped; t_fail = first crossing of
    ``target * threshold_frac``. Censored (never reaches the threshold
    within the run): flat at the cap.

    ``target`` is the scenario's target severity from SCENARIOS
    (e.g. 1.0 bearing, 0.7 impeller). The per-mode threshold is intentional:
    an impeller at 70 % damage is never going to reach severity 1.0, but it
    still has a defined intervention point.
    """
    sev = frame["fault_severity"].to_numpy(dtype=float)
    t = frame["t"].to_numpy(dtype=float)
    thr = max(target * threshold_frac, 1e-9)
    hits = np.where(sev >= thr)[0]
    if hits.size == 0:
        return np.full(len(frame), cap_s, dtype=float)
    t_fail = float(t[hits[0]])
    return np.clip(t_fail - t, 0.0, cap_s)


def evaluate_rul(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    return {
        "mae_s": round(float(mean_absolute_error(y_true, y_pred)), 1),
        "rmse_s": round(float(np.sqrt(mean_squared_error(y_true, y_pred))), 1),
        "mae_min": round(float(mean_absolute_error(y_true, y_pred)) / 60.0, 1),
        "n": int(len(y_true)),
    }


def interval_coverage(y_true: np.ndarray, lo: np.ndarray, hi: np.ndarray) -> float:
    """Fraction of true RUL values inside the [lo, hi] interval."""
    return float(np.mean((y_true >= lo) & (y_true <= hi)))


# ---------------------------------------------------------------------------
# models
# ---------------------------------------------------------------------------


class RidgeRUL:
    """Linear baseline."""

    def __init__(self, alpha: float = 1.0):
        self.model = Ridge(alpha=alpha)

    def fit(self, X: pd.DataFrame, rul: np.ndarray) -> "RidgeRUL":
        self.model.fit(X, rul)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return self.model.predict(X)


class GradientBoostingRUL:
    """Mean RUL by gradient boosting (the classical tabular method)."""

    def __init__(self, n_estimators: int = 250, max_depth: int = 4,
                 learning_rate: float = 0.05, random_state: int = 42):
        self.model = GradientBoostingRegressor(
            n_estimators=n_estimators, max_depth=max_depth,
            learning_rate=learning_rate, random_state=random_state)

    def fit(self, X: pd.DataFrame, rul: np.ndarray) -> "GradientBoostingRUL":
        self.model.fit(X, rul)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return self.model.predict(X)

    @property
    def raw_model(self):
        return self.model


class QuantileGradientBoostingRUL:
    """RUL with prediction intervals via quantile gradient boosting.

    Train one GBM per quantile (loss='quantile'). The interval is a
    calibrated-in-distribution uncertainty estimate; coverage on held-out
    assets is measured and reported (never assumed).
    """

    def __init__(self, quantiles: Sequence[float] = (0.10, 0.50, 0.90),
                 n_estimators: int = 200, max_depth: int = 4,
                 learning_rate: float = 0.05, random_state: int = 42):
        self.quantiles = tuple(quantiles)
        self.models: Dict[float, GradientBoostingRegressor] = {}
        self._params = dict(n_estimators=n_estimators, max_depth=max_depth,
                            learning_rate=learning_rate,
                            random_state=random_state)

    def fit(self, X: pd.DataFrame, rul: np.ndarray) -> "QuantileGradientBoostingRUL":
        for q in self.quantiles:
            m = GradientBoostingRegressor(
                loss="quantile", alpha=q, **self._params)
            m.fit(X, rul)
            self.models[q] = m
        return self

    def predict(self, X: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        lo = self.models[self.quantiles[0]].predict(X)
        med = self.models[self.quantiles[1]].predict(X)
        hi = self.models[self.quantiles[2]].predict(X)
        return lo, med, hi

    @property
    def median_model(self):
        return self.models[self.quantiles[1]]


@dataclass
class WindowMLPRegressor:
    """Temporal RUL model: MLP over sliding windows of standardised sensors.

    Windows of ``window`` consecutive samples (flattened) are fed to a small
    MLP that regresses RUL at the window's end. Causal: a window never sees
    the future. Segments are split per asset (a reset of t = 0) so windows
    never straddle assets.
    """

    window: int = 32
    sensors: Optional[List[str]] = None
    hidden: Tuple[int, int] = (64, 16)
    cap_s: float = DEFAULT_CAP_S
    seed: int = 42
    epochs: int = 25
    lr: float = 1e-3
    batch: int = 256
    stride: int = 4
    patience: int = 5
    device: str = "auto"

    def __post_init__(self):
        import torch
        self._torch = torch
        torch.manual_seed(self.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.seed)
        if self.device not in ("auto", "cpu", "cuda"):
            raise ValueError(f"unknown device {self.device!r}")
        self._device = torch.device(
            self.device if self.device != "auto"
            else ("cuda" if torch.cuda.is_available() else "cpu"))
        if self._device.type == "cuda" and not torch.cuda.is_available():
            raise ValueError("device='cuda' requested but CUDA is not available")
        self._model = None
        self._stats: Dict[int, Tuple[float, float]] = {}

    # -- data plumbing -------------------------------------------------
    @staticmethod
    def _windows(F: np.ndarray, W: int, stride: int) -> Tuple[np.ndarray, np.ndarray]:
        n = F.shape[0]
        ends = np.arange(W - 1, n, stride)
        idx = np.arange(W)[None, :] + (ends - (W - 1))[:, None]
        return F[idx].reshape(len(ends), W * F.shape[1]), ends

    def _standardize(self, X: pd.DataFrame) -> np.ndarray:
        cols = self.sensors or [c for c in X.columns if c not in ("t", "u")]
        cols = [c for c in cols if c in X.columns]
        self.sensors = cols
        F = X[cols].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
        if not self._stats:
            for j in range(F.shape[1]):
                sd = float(np.std(F[:, j]))
                self._stats[j] = (float(np.mean(F[:, j])), sd if sd > 1e-12 else 1.0)
        S = np.empty_like(F)
        for j in range(F.shape[1]):
            mu, sd = self._stats[j]
            S[:, j] = (F[:, j] - mu) / sd if sd > 0 else F[:, j] * 0.0
        return S

    def _segments(self, X: pd.DataFrame, rul: np.ndarray) -> List[Tuple[pd.DataFrame, np.ndarray]]:
        """Split into contiguous segments at resets of t (asset boundaries)."""
        t = X["t"].to_numpy(dtype=float)
        bounds = [0]
        for i in range(1, len(t)):
            if t[i] < t[i - 1]:
                bounds.append(i)
        bounds.append(len(t))
        segs = []
        for a, b in zip(bounds[:-1], bounds[1:]):
            if b - a >= self.window:
                segs.append((X.iloc[a:b], rul[a:b]))
        return segs

    # -- training / scoring --------------------------------------------
    def fit(self, X: pd.DataFrame, rul: np.ndarray) -> "WindowMLPRegressor":
        import torch
        import torch.nn as nn
        Xw_list, y_list = [], []
        for seg_X, seg_r in self._segments(X, rul):
            S = self._standardize(seg_X)
            W, e = self._windows(S, self.window, self.stride)
            Xw_list.append(W)
            y_list.append(seg_r[e])
        if not Xw_list:
            raise ValueError("no segments long enough for a window")
        Xw = np.concatenate(Xw_list)
        y = np.concatenate(y_list) / self.cap_s

        wd = Xw.shape[1]
        layers = []
        prev = wd
        for h in self.hidden:
            layers += [nn.Linear(prev, h), nn.ReLU()]
            prev = h
        layers.append(nn.Linear(prev, 1))
        model = nn.Sequential(*layers)
        self._model = _train_rul_mlp(model, Xw, y, self.epochs, self.lr,
                                     self.batch, self.patience, self.seed,
                                     device=self._device)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if self._model is None:
            raise RuntimeError("predict() before fit()")
        preds = []
        for seg_X, _ in self._segments(X, np.zeros(len(X))):
            S = self._standardize(seg_X)
            W, e = self._windows(S, self.window, self.stride)
            with self._torch.no_grad():
                p = self._model(self._torch.tensor(
                    W, dtype=self._torch.float32, device=self._device))
            preds.append(p.cpu().numpy().ravel())
        if not preds:
            return np.zeros(len(X))
        return np.concatenate(preds) * self.cap_s


def _train_rul_mlp(model, Xw: np.ndarray, y: np.ndarray,
                   epochs: int, lr: float, batch: int, patience: int,
                   seed: int = 0, val_frac: float = 0.1,
                   device: Optional[object] = None) -> object:
    """PyTorch training loop with early stopping on a *random* holdout.

    The validation slice is a seeded random draw (not the tail of the
    series): with time-series RUL targets the tail is systematically RUL ~ 0,
    so a tail holdout makes early stopping stall almost immediately.
    Tensors and the network live on ``device`` (CPU here; CUDA when one is
    present - the CUDA branch is not exercisable on this machine and is
    documented as such in the PR).
    """
    import torch
    import torch.nn as nn
    if device is None:
        device = torch.device("cpu")
    torch.manual_seed(seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(seed)
    model.to(device)
    Xt = torch.tensor(Xw, dtype=torch.float32, device=device)
    yt = torch.tensor(y, dtype=torch.float32, device=device).reshape(-1, 1)
    rng = np.random.default_rng(seed)
    n = Xt.shape[0]
    n_val = max(1, int(round(n * val_frac)))
    perm = rng.permutation(n)
    val_idx, tr_idx = perm[:n_val], perm[n_val:]
    Xtr, ytr = Xt[tr_idx], yt[tr_idx]
    Xva, yva = Xt[val_idx], yt[val_idx]
    loader = torch.utils.data.DataLoader(
        torch.utils.data.TensorDataset(Xtr, ytr), batch_size=batch, shuffle=True)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()
    # Early stopping is only meaningful when the holdout is large enough to
    # be a stable estimate of generalisation (>= ~100 samples). For small
    # datasets (unit tests, low-sample assets) we train the fixed budget and
    # log the holdout curve instead - the final weights are returned.
    use_early_stop = n_val >= 100
    best, bad = float("inf"), 0
    best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
    for _ in range(epochs):
        model.train()
        for xb, yb in loader:
            opt.zero_grad()
            loss = loss_fn(model(xb), yb)
            loss.backward()
            opt.step()
        model.eval()
        with torch.no_grad():
            vloss = float(loss_fn(model(Xva), yva))
        if not use_early_stop:
            continue
        if vloss < best - 1e-6:
            best, bad = vloss, 0
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        else:
            bad += 1
            if bad >= patience:
                break
    if use_early_stop:
        model.load_state_dict(best_state)
    model.eval()
    return model