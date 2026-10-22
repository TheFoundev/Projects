"""The API of the outlier benchmark.

The four detectors of the project are fitted on the normal points of every
dataset and scored with the ROC AUC of the project, so the console shows the
real comparison between the z-score, the isolation forest, the local outlier
factor and the one class SVM.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from src.data import load_data  # noqa: E402
from src.model import train  # noqa: E402

#: The fitted detectors, kept between the calls.
_CACHE: dict[int, tuple] = {}


def _state(seed: int = 42):
    """The datasets, the fitted detectors and the metrics of the run."""
    if seed not in _CACHE:
        data = load_data(seed=seed)
        model, metrics = train(data)
        _CACHE[seed] = (data, model, metrics)
    return _CACHE[seed]


def _number(payload, key: str, default: int) -> int:
    """One number of the request; a query string arrives as a list."""
    value = (payload or {}).get(key, default)
    if isinstance(value, (list, tuple)):
        value = value[0] if value else default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def summary():
    data, model, metrics = _state()
    scores = model["scores"]

    # The mean AUC of every detector over the three datasets.
    detectors = sorted({detector for row in scores.values() for detector in row})
    means = [
        {
            "detector": detector,
            "mean_auc": round(float(np.mean([scores[name][detector] for name in scores])), 4),
        }
        for detector in detectors
    ]
    means.sort(key=lambda row: row["mean_auc"], reverse=True)

    rows = []
    for name, row in scores.items():
        for detector, value in row.items():
            rows.append({"dataset": name, "detector": detector, "auc": value})

    return {
        "stats": {
            "best_auc": metrics["best_mean_auc"],
            "best_detector": metrics["best_detector"],
            "detectors": metrics["detectors"],
            "datasets": metrics["datasets"],
        },
        "series": [{"label": row["detector"], "value": row["mean_auc"]} for row in means],
        "lists": {
            "auc": rows,
            "detectors": means,
            "datasets": [
                {"dataset": name, "points": int(len(X)), "outliers": int(y.sum())}
                for name, (X, y) in data["datasets"].items()
            ],
        },
    }


def handle(method, path, payload, user):
    if method == "GET" and path == "/api/scores":
        seed = _number(payload, "seed", 42)
        _, model, _ = _state(seed)
        return 200, {"scores": model["scores"]}

    if method == "POST" and path == "/api/train":
        seed = _number(payload, "seed", 42)
        _CACHE.pop(seed, None)
        state = summary()
        return 200, {"retrained": True, "summary": state}

    return 404, {"error": "not found"}
