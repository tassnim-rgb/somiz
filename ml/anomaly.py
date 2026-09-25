"""Anomaly detection detectors for streaming/asset sensors.

Four methods are implemented behind one interface, from cheapest to most
expressive (the full comparison — including detection delay and false-alarm
rate at matched operating points — is the anomaly experiment in
scripts/run_anomaly_experiment.py):

  1. StatisticalBaselineDetector  — control-chart style: persistent
     deviations of standardised signals from a healthy baseline. Baseline,
     cheap, interpretable.
  2. IsolationForestDetector      — tree-ensemble isolation on the feature
     frame (rolling statistics included). Baseline-vs.-complex method #2.
  3. PointAutoencoderDetector     — PyTorch undercomplete autoencoder on
     standardised sensor vectors; score = reconstruction error.
  4. WindowedAutoencoderDetector  — temporal method: autoencoder on
     sliding windows of W consecutive samples (learns temporal structure);
     score per window assigned to its end sample.

All detectors: ``fit`` on HEALTHY data only (no anomaly labels — truly
unsupervised), then ``score`` every sample. Thresholding, persistence and
evaluation live in ml/evaluate.py.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


class AnomalyDetector(ABC):
    """Common interface: fit on healthy data, emit per-sample anomaly scores."""

    @abstractmethod
    def fit(self, X: pd.DataFrame) -> "AnomalyDetector":
        ...

    @abstractmethod
    def score(self, X: pd.DataFrame) -> np.ndarray:
        """Higher score = more anomalous. Length must equal len(X)."""


# ---------------------------------------------------------------------------
# 1. Statistical baseline (persistent control-chart)
# ---------------------------------------------------------------------------


class StatisticalBaselineDetector(AnomalyDetector):
    """RMS z-score over a healthy-standardised sensor set, with persistence
    handled at evaluation time (see ml/evaluate.persist_flags)."""

    def __init__(self, sensors: Optional[List[str]] = None, smooth: int = 30):
        self.sensors = list(sensors) if sensors else []
        self.smooth = smooth
        self._stats: dict = {}

    def fit(self, X: pd.DataFrame) -> "StatisticalBaselineDetector":
        cols = self.sensors or [c for c in X.columns if c not in ("t", "u")]
        cols = [c for c in cols if c in X.columns]
        if not cols:
            raise ValueError("no usable sensor columns")
        self.sensors = cols
        self._stats = {}
        for c in cols:
            v = X[c].to_numpy(dtype=float)
            v = v[np.isfinite(v)]
            sd = float(np.std(v))
            if sd < 1e-12:
                sd = 1.0
            self._stats[c] = (float(np.mean(v)), sd)
        return self

    def score(self, X: pd.DataFrame) -> np.ndarray:
        if not self._stats:
            raise RuntimeError("score() before fit()")
        z = np.stack([
            (X[c].to_numpy(dtype=float) - self._stats[c][0]) / self._stats[c][1]
            for c in self.sensors
        ], axis=1)
        # RMS over sensors, per sample
        s = np.sqrt(np.nanmean(z ** 2, axis=1))
        s = np.nan_to_num(s, nan=0.0)
        if self.smooth > 1:
            s = pd.Series(s).rolling(self.smooth, min_periods=1).mean().to_numpy()
        return s


# ---------------------------------------------------------------------------
# 2. Isolation Forest on the feature frame
# ---------------------------------------------------------------------------


class IsolationForestDetector(AnomalyDetector):
    def __init__(self, contamination: float = 0.05, n_estimators: int = 200,
                 random_state: int = 42, feature_cols: Optional[List[str]] = None):
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.feature_cols = list(feature_cols) if feature_cols else []
        self._model: Optional[IsolationForest] = None

    def _frame(self, X: pd.DataFrame) -> pd.DataFrame:
        cols = self.feature_cols or [c for c in X.columns if c not in ("t", "u")]
        cols = [c for c in cols if c in X.columns]
        return X[cols].apply(pd.to_numeric, errors="coerce").fillna(0.0)

    def fit(self, X: pd.DataFrame) -> "IsolationForestDetector":
        F = self._frame(X)
        self.feature_cols = list(F.columns)
        self._model = IsolationForest(
            contamination=self.contamination,
            n_estimators=self.n_estimators,
            random_state=self.random_state,
            n_jobs=-1,
        ).fit(F)
        return self

    def score(self, X: pd.DataFrame) -> np.ndarray:
        if self._model is None:
            raise RuntimeError("score() before fit()")
        # decision_function: +1 normal .. -1 anomalous -> negate so higher = anomalous
        return -self._model.decision_function(self._frame(X))


# ---------------------------------------------------------------------------
# 3 + 4. PyTorch autoencoders
# ---------------------------------------------------------------------------

try:
    import torch  # noqa: E402
    import torch.nn as nn  # noqa: E402

    torch.set_num_threads(max(1, torch.get_num_threads()))
    _TORCH_AVAILABLE = True
except ImportError:  # torch is optional: only the autoencoder detectors need it
    torch = None  # type: ignore[assignment]
    nn = None  # type: ignore[assignment]
    _TORCH_AVAILABLE = False


def _require_torch() -> None:
    """Raise a clear error if a PyTorch autoencoder is used without torch."""
    if not _TORCH_AVAILABLE:
        raise RuntimeError(
            "PyTorch autoencoder detectors require the optional 'torch' "
            "package, which is not installed in this environment. Use "
            "StatisticalBaselineDetector or IsolationForestDetector instead."
        )


def _train_ae(model: nn.Module, X: np.ndarray, seed: int, epochs: int,
              lr: float, batch: int, patience: int) -> nn.Module:
    _require_torch()
    torch.manual_seed(seed)
    Xt = torch.tensor(X, dtype=torch.float32)
    n = Xt.shape[0]
    n_val = max(1, n // 10)
    Xtr, Xva = Xt[:n - n_val], Xt[n - n_val:]
    loader = torch.utils.data.DataLoader(
        torch.utils.data.TensorDataset(Xtr, Xtr), batch_size=batch, shuffle=True)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()
    best = float("inf")
    best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
    bad = 0
    for ep in range(epochs):
        model.train()
        for xb, _ in loader:
            opt.zero_grad()
            loss = loss_fn(model(xb), xb)
            loss.backward()
            opt.step()
        model.eval()
        with torch.no_grad():
            vloss = float(loss_fn(model(Xva), Xva))
        if vloss < best - 1e-6:
            best = vloss
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
            bad = 0
        else:
            bad += 1
            if bad >= patience:
                break
    model.load_state_dict(best_state)
    model.eval()
    return model


def _scores(model: nn.Module, X: np.ndarray) -> np.ndarray:
    _require_torch()
    with torch.no_grad():
        out = model(torch.tensor(X, dtype=torch.float32))
        s = ((out - torch.tensor(X, dtype=torch.float32)) ** 2).mean(dim=1).numpy()
    return s


class PointAutoencoderDetector(AnomalyDetector):
    """Undercomplete point autoencoder on standardised sensor vectors."""

    def __init__(self, sensors: Optional[List[str]] = None, hidden: tuple = (32, 8),
                 seed: int = 42, epochs: int = 30, lr: float = 1e-3,
                 batch: int = 128, patience: int = 5):
        self.sensors = list(sensors) if sensors else []
        self.hidden = hidden
        self.seed = seed
        self.epochs = epochs
        self.lr = lr
        self.batch = batch
        self.patience = patience
        self._stats: dict = {}
        self._model: Optional[nn.Module] = None

    def _frame(self, X: pd.DataFrame) -> np.ndarray:
        cols = self.sensors or [c for c in X.columns if c not in ("t", "u")]
        cols = [c for c in cols if c in X.columns]
        F = X[cols].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
        return np.nan_to_num(F, nan=0.0), cols

    def _standardize(self, F: np.ndarray) -> np.ndarray:
        S = np.empty_like(F)
        for j in range(F.shape[1]):
            col = F[:, j]
            mu, sd = self._stats[j]
            S[:, j] = (col - mu) / sd if sd > 0 else col * 0.0
        return S

    def fit(self, X: pd.DataFrame) -> "PointAutoencoderDetector":
        F, cols = self._frame(X)
        self.sensors = cols
        self._stats = {}
        for j in range(F.shape[1]):
            sd = float(np.std(F[:, j]))
            self._stats[j] = (float(np.mean(F[:, j])), sd if sd > 1e-12 else 1.0)
        S = self._standardize(F)
        d = S.shape[1]
        layers = []
        prev = d
        for h in self.hidden:
            layers += [nn.Linear(prev, h), nn.ReLU()]
            prev = h
        layers += [nn.Linear(prev, d)]
        self._model = _train_ae(nn.Sequential(*layers), S, self.seed,
                                self.epochs, self.lr, self.batch, self.patience)
        return self

    def score(self, X: pd.DataFrame) -> np.ndarray:
        if self._model is None:
            raise RuntimeError("score() before fit()")
        F, cols = self._frame(X)
        S = self._standardize(F)
        return _scores(self._model, S)


class WindowedAutoencoderDetector(AnomalyDetector):
    """Temporal method: autoencoder over sliding windows of W samples.

    Trained on healthy windows; reconstruction error per window is assigned
    to the window's end sample (standard causal padding for the first W-1
    rows: they receive the first window's score).
    """

    def __init__(self, window: int = 32, sensors: Optional[List[str]] = None,
                 hidden: tuple = (64, 16), seed: int = 42, epochs: int = 25,
                 lr: float = 1e-3, batch: int = 128, patience: int = 5):
        self.window = window
        self.sensors = list(sensors) if sensors else []
        self.hidden = hidden
        self.seed = seed
        self.epochs = epochs
        self.lr = lr
        self.batch = batch
        self.patience = patience
        self._stats: dict = {}
        self._model: Optional[nn.Module] = None

    def _frame(self, X: pd.DataFrame) -> np.ndarray:
        cols = self.sensors or [c for c in X.columns if c not in ("t", "u")]
        cols = [c for c in cols if c in X.columns]
        F = X[cols].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
        return np.nan_to_num(F, nan=0.0), cols

    @staticmethod
    def _windows(F: np.ndarray, W: int) -> np.ndarray:
        n, d = F.shape
        # vectorised strided windows
        idx = np.arange(W)[None, :] + np.arange(n - W + 1)[:, None]
        return F[idx].reshape(n - W + 1, W * d)

    def fit(self, X: pd.DataFrame) -> "WindowedAutoencoderDetector":
        F, cols = self._frame(X)
        self.sensors = cols
        self._stats = {}
        for j in range(F.shape[1]):
            sd = float(np.std(F[:, j]))
            self._stats[j] = (float(np.mean(F[:, j])), sd if sd > 1e-12 else 1.0)
        S = self._standardize(F)
        W = min(self.window, S.shape[0])
        if W < 8:
            raise ValueError(f"need >= 8 samples for a window, got {S.shape[0]}")
        Xw = self._windows(S, W)
        wd = Xw.shape[1]
        layers = []
        prev = wd
        for h in self.hidden:
            layers += [nn.Linear(prev, h), nn.ReLU()]
            prev = h
        layers += [nn.Linear(prev, wd)]
        self._window = W
        self._model = _train_ae(nn.Sequential(*layers), Xw, self.seed,
                                self.epochs, self.lr, self.batch, self.patience)
        return self

    def _standardize(self, F: np.ndarray) -> np.ndarray:
        S = np.empty_like(F)
        for j in range(F.shape[1]):
            mu, sd = self._stats[j]
            S[:, j] = (F[:, j] - mu) / sd if sd > 0 else F[:, j] * 0.0
        return S

    def score(self, X: pd.DataFrame) -> np.ndarray:
        if self._model is None:
            raise RuntimeError("score() before fit()")
        W = self._window
        F, cols = self._frame(X)
        S = self._standardize(F)
        n = S.shape[0]
        scores = np.full(n, np.nan)
        if n < W:
            return np.zeros(n)
        Xw = self._windows(S, W)
        sw = _scores(self._model, Xw)
        scores[W - 1:] = sw
        scores[:W - 1] = sw[0]  # causal padding with first window score
        return scores