"""The domain logic behind the API of the explainability demo.

The model is really trained and the attributions really computed with the
kernel SHAP values; the report shows the importance of the features and the
explanation of one row.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.data import load_data  # noqa: E402
from src.model import explain, global_importance, train  # noqa: E402

_STATE = {}


def _model():
    if "model" not in _STATE:
        data = load_data(seed=42, quick=True)
        model, metrics = train(data, quick=True)
        explainer, values = explain(model, data, rows=8, quick=True)
        importance = {row["feature"]: row["importance"] for row in global_importance(values, data["features"])}
        _STATE["model"] = (model, metrics, data, importance)
    return _STATE["model"]


def summary():
    model, metrics, data, importance = _model()
    ranked = sorted(importance.items(), key=lambda item: abs(item[1]), reverse=True)
    return {
        "stats": {
            "features": metrics["features"],
            "rows_explained": 8,
            "top_feature": metrics["top_feature"],
            "top_weight": metrics["top_importance"],
            "r2": metrics["r2"],
        },
        "series": [{"label": name, "value": round(abs(weight), 4)} for name, weight in ranked],
        "lists": {
            "features": [
                {"feature": name, "weight": round(weight, 4)} for name, weight in ranked
            ]
        },
    }


def handle(method, path, payload, user):
    if method == "GET" and path.endswith("/features"):
        return 200, {"features": summary()["lists"]["features"]}
    return 404, {"error": "not found"}
