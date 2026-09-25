"""Model-agnostic explainability for diagnosis / RUL models.

SHAP (TreeExplainer) gives an exact, game-theoretic attribution for tree
ensembles: how much each feature pushed a prediction away from the expected
value. We expose two serialisable summaries via `shap`:

  - ``shap_feature_importance``  : global mean |SHAP| per feature
                                   (per class for classifiers);
  - ``shap_sample_explanation``  : per-prediction feature attributions for
                                   one row (for a narrative use case).

Both keep the raw values and ranks, so the numbers are traceable, and never
claim more than the model they explain (the same simulated caveats apply).
"""

from __future__ import annotations

from typing import List, Optional, Sequence

import numpy as np
import pandas as pd

REQUIRES = "run with `pip install shap` (declared in requirements.txt)"


def _explainer(model):
    import shap
    try:
        return shap.TreeExplainer(model)
    except Exception as exc:  # pragma: no cover - defensive
        raise RuntimeError(f"TreeExplainer failed for {type(model).__name__}: {exc}")


def _per_class_arrays(values) -> list:
    """Normalise TreeExplainer output to ``[class_0_arr, class_1_arr, ...]``.

    shap returns, depending on version / model:
      - a list of per-class arrays for classifiers;
      - one ``(samples, features, classes)`` ndarray (e.g. shap >= 0.52
        with sklearn classifiers);
      - one ``(samples, features)`` ndarray for single-output models.
    """
    if isinstance(values, list):
        return [np.asarray(v) for v in values]
    arr = np.asarray(values)
    if arr.ndim == 3:  # (samples, features, classes)
        return [arr[..., k] for k in range(arr.shape[2])]
    return [arr]


def shap_feature_importance(
    model,
    X: pd.DataFrame,
    class_names: Optional[Sequence[str]] = None,
    n_background: int = 300,
    seed: int = 42,
    top_k: int = 10,
) -> dict:
    """Global mean |SHAP| per feature; per class for classifiers
    (multi-output), otherwise single-output."""
    import shap  # noqa: F401
    rng = np.random.default_rng(seed)
    n = min(n_background, len(X))
    idx = rng.choice(len(X), size=n, replace=False)
    Xb = X.iloc[idx]
    explainer = _explainer(model)
    raw = explainer.shap_values(Xb)
    arrays = _per_class_arrays(raw)
    features = list(Xb.columns)

    if len(arrays) > 1:
        # multi-class classifier
        names = list(class_names) if class_names is not None \
            else [f"class_{i}" for i in range(len(arrays))]
        out = {}
        for cls, arr in zip(names, arrays):
            mean_abs = np.abs(arr).mean(axis=0)
            order = np.argsort(-mean_abs)
            out[str(cls)] = {
                "top_features": [
                    {"feature": features[i], "mean_abs_shap": round(float(mean_abs[i]), 5)}
                    for i in order[:top_k]
                ],
                "n_background": n,
            }
        return {"type": "classifier", "per_class": out, "features": features}
    # single-output regressor
    mean_abs = np.abs(arrays[0]).mean(axis=0)
    order = np.argsort(-mean_abs)
    return {
        "type": "regressor",
        "top_features": [
            {"feature": features[i], "mean_abs_shap": round(float(mean_abs[i]), 5)}
            for i in order[:top_k]
        ],
        "n_background": n,
        "features": features,
    }


def shap_sample_explanation(
    model,
    X_row: pd.DataFrame,
    feature_names: List[str],
    class_index: Optional[int] = None,
) -> dict:
    """Per-prediction attribution for a single row.

    For a regressor: contributions of each feature to the prediction.
    For a classifier: contributions to the given class logit
    (``class_index``), which is what drives the predicted label.
    """
    import shap  # noqa: F401
    explainer = _explainer(model)
    row = X_row.iloc[[0]]
    raw = explainer.shap_values(row)
    arrays = _per_class_arrays(raw)
    if len(arrays) > 1:
        arr = arrays[class_index if class_index is not None else 0].reshape(-1)
    else:
        arr = arrays[0].reshape(-1)
    features = list(feature_names)
    order = np.argsort(-np.abs(arr))
    return {
        "contributions": [
            {"feature": features[i],
             "shap": round(float(arr[i]), 5),
             "direction": "pushes prediction up" if arr[i] > 0 else "pushes prediction down"}
            for i in order[:10]
        ],
        "explained_class_index": class_index,
    }