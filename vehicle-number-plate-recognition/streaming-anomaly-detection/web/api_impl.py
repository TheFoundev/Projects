"""The API of the streaming anomaly detector.

The numbers are the real ones: the stream is made by the project, the
detector of the project walks it point by point and the threshold is fitted
on the stream by trying every candidate. The precision, the recall and the F1
are measured against the labels of the stream, so the console shows what the
detector really finds.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from src.data import load_data  # noqa: E402
from src.model import evaluate, simulate, train  # noqa: E402

#: The stream and the fitted threshold of every seed.
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
    """The stream, the model and the metrics of the run."""
    if seed not in _CACHE:
        data = load_data(seed=seed)
        model, metrics = train(data)
        _CACHE[seed] = (data, model, metrics)
    return _CACHE[seed]


def _anomalies(data, model) -> list[dict]:
    """The points of the stream the detector flagged."""
    values = data["values"]
    labels = data["labels"]
    scores, flags = simulate(values, threshold=model["threshold"])
    rows = []
    for index in np.nonzero(flags)[0]:
        rows.append({
            "point": int(index),
            "value": round(float(values[index]), 2),
            "score": round(float(scores[index]), 2),
            "real anomaly": "yes" if labels[index] == 1 else "no",
        })
    return rows


def summary():
    data, model, metrics = _state()
    rows = _anomalies(data, model)

    return {
        "stats": {
            "f1": metrics["f1"],
            "precision": metrics["precision"],
            "recall": metrics["recall"],
            "threshold": metrics["threshold"],
        },
        "series": [
            {"label": f"point {row['point']}", "value": row["score"]}
            for row in rows
        ],
        "lists": {
            "anomalies": rows,
        },
    }


def handle(method, path, payload, user):
    if method == "GET" and path == "/api/anomalies":
        data, model, _metrics = _state()
        return 200, {"anomalies": _anomalies(data, model)}

    if method == "POST" and path == "/api/train":
        seed = _number(payload, "seed", 42)
        _CACHE.pop(seed, None)
        state = summary()
        return 200, {"retrained": True, "summary": state}

    return 404, {"error": "not found"}
