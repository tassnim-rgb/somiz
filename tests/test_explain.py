"""Phase 5 tests: SHAP explainability wrappers (tiny forests, fast)."""

import numpy as np
import pandas as pd
import pytest

from sklearn.ensemble import GradientBoostingRegressor, RandomForestClassifier

from ml.explain import shap_feature_importance, shap_sample_explanation


def _data(seed=0, n=250):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, 6))
    Xdf = pd.DataFrame(X, columns=[f"f{i}" for i in range(6)])
    y_cls = (X[:, 0] + X[:, 1] > 0).astype(int)
    y_reg = X[:, 2] * 40.0 + X[:, 3] * 10.0 + rng.normal(0, 5, n)
    return Xdf, y_cls, y_reg


def test_classifier_feature_importance_ranks_drivers():
    X, y, _ = _data()
    rf = RandomForestClassifier(n_estimators=30, max_depth=4,
                                random_state=0).fit(X, y)
    out = shap_feature_importance(rf, X, class_names=["0", "1"], n_background=120)
    assert out["type"] == "classifier"
    assert set(out["per_class"]) == {"0", "1"}
    top0 = out["per_class"]["0"]["top_features"]
    assert len(top0) == len(X.columns)  # fewer features than top_k -> all 6
    top_names = [t["feature"] for t in top0]
    # f0 + f1 are the label drivers and must dominate the attributions
    assert top_names[0] in ("f0", "f1")
    assert top_names[1] in ("f0", "f1")
    assert top0[0]["mean_abs_shap"] > 0


def test_regressor_feature_importance():
    X, _, y = _data()
    gb = GradientBoostingRegressor(n_estimators=30, max_depth=3,
                                   random_state=0).fit(X, y)
    out = shap_feature_importance(gb, X, n_background=120)
    assert out["type"] == "regressor"
    top = [t["feature"] for t in out["top_features"]]
    assert "f2" in top  # strongest driver present in the top-10
    assert out["top_features"][0]["mean_abs_shap"] > 0


def test_sample_explanation_schema():
    X, y, _ = _data(seed=2)
    rf = RandomForestClassifier(n_estimators=30, max_depth=4,
                                random_state=0).fit(X, y)
    row = X.iloc[[0]]
    out = shap_sample_explanation(rf, row, list(X.columns), class_index=1)
    assert len(out["contributions"]) == len(X.columns)  # 6 features
    assert out["explained_class_index"] == 1
    assert all(c["direction"] in ("pushes prediction up", "pushes prediction down")
               for c in out["contributions"])
    assert all(c["feature"] in list(X.columns) for c in out["contributions"])