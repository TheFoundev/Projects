"""The API of the time series classifier.

The numbers are the real ones: the series are made by the project, the
features and the forest are the ones of the project and the accuracy is
measured on the series the forest did not see. The confusion matrix is built
from that same prediction, so the console shows which shape the classifier
really mixes up with which one.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from src.data import load_data  # noqa: E402
from src.model import featurize, train  # noqa: E402

#: The series, the forest and the metrics of every seed.
_CACHE: dict[int, tuple] = {}


def _number(payload, key: str, default: int) -> int:
    """One number of the request.

    The query string of a GET arrives as a dictionary of lists, so the first
    value of the list is taken.
    """
    value = (payload or {}).get(key, default)
    if isinstance(value, (list, tuple)):
        value = value[0] if value else default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _state(seed: int = 42):
    """The series, the trained forest and the metrics of the run."""
    if seed not in _CACHE:
        data = load_data(seed=seed)
        model, metrics = train(data)
        _CACHE[seed] = (data, model, metrics)
    return _CACHE[seed]


def _confusion(data, model) -> list[dict]:
    """The confusion matrix of the run, one row per pair of shapes."""
    classes = data["classes"]
    truth = data["y_test"]
    prediction = model.predict(featurize(data["X_test"]))
    rows = []
    for true_index, true_name in enumerate(classes):
        for predicted_index, predicted_name in enumerate(classes):
            count = int(np.sum((truth == true_index) & (prediction == predicted_index)))
            if count:
                rows.append({
                    "true": true_name,
                    "predicted": predicted_name,
                    "series": count,
                })
    return rows


def _per_class(data, model) -> list[dict]:
    """The share of the series of every class the classifier got right."""
    classes = data["classes"]
    truth = data["y_test"]
    prediction = model.predict(featurize(data["X_test"]))
    rows = []
    for index, name in enumerate(classes):
        total = int(np.sum(truth == index))
        correct = int(np.sum((truth == index) & (prediction == index)))
        rows.append({
            "class": name,
            "correct": correct,
            "total": total,
            "accuracy": round(correct / total, 4) if total else 0.0,
        })
    return rows


def summary():
    data, model, metrics = _state()
    rows = _per_class(data, model)

    return {
        "stats": {
            "accuracy": metrics["accuracy"],
            "test_series": metrics["test_series"],
            "sine_correct": metrics["sine_correct"],
            "trend_correct": metrics["trend_correct"],
        },
        "series": [
            {"label": row["class"], "value": row["accuracy"]}
            for row in rows
        ],
        "lists": {
            "confusion": _confusion(data, model),
        },
    }


def handle(method, path, payload, user):
    if method == "GET" and path == "/api/confusion":
        data, model, _metrics = _state()
        return 200, {"confusion": _confusion(data, model)}

    if method == "POST" and path == "/api/train":
        seed = _number(payload, "seed", 42)
        _CACHE.pop(seed, None)
        state = summary()
        return 200, {"retrained": True, "summary": state}

    return 404, {"error": "not found"}
