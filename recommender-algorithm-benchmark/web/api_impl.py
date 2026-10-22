"""The API of the recommender benchmark.

The four recommenders of the project are fitted on the same ratings and
measured with the same loop: the popularity, the item-item cosine, the SVD and
the NMF all get a precision@5, a recall@5 and a catalogue coverage, and the
console shows them side by side.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.data import load_data  # noqa: E402
from src.model import evaluate, recommend_matrix, train  # noqa: E402

#: The fitted recommenders, kept between the calls.
_CACHE: dict[int, tuple] = {}


def _state(seed: int = 42):
    """The data, the fitted recommenders and the metrics of the run."""
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


def _recommendations(data, model, method: str, user: int, count: int = 5) -> list[dict]:
    """The items the model proposes to one user, with their score."""
    scores = model["scores"][method]
    items = recommend_matrix(scores, model["seen"], user, count)
    return [
        {"title": data["titles"][item], "item": int(item), "score": round(float(scores[user][item]), 3)}
        for item in items
    ]


def summary():
    data, model, metrics = _state()
    results = evaluate(model, data)
    rows = [
        {"method": name, "precision": round(float(values["precision"]), 4),
         "recall": round(float(values["recall"]), 4),
         "coverage": round(float(values["coverage"]), 4)}
        for name, values in results.items()
    ]
    rows.sort(key=lambda row: row["precision"], reverse=True)

    return {
        "stats": {
            "best_precision": metrics["best_precision_at_5"],
            "best_recall": metrics["best_recall_at_5"],
            "methods": metrics["methods"],
            "items": metrics["items"],
        },
        "series": [{"label": row["method"], "value": row["precision"]} for row in rows],
        "lists": {
            "methods": rows,
            "recommendations": _recommendations(data, model, metrics["best_method"], 0),
        },
    }


def handle(method, path, payload, user):
    if method == "GET" and path == "/api/recommendations":
        seed = _number(payload, "seed", 42)
        user_index = _number(payload, "user", 0)
        data, model, metrics = _state(seed)
        wanted = str((payload or {}).get("method", metrics["best_method"]))
        if isinstance(wanted, list):
            wanted = wanted[0] if wanted else metrics["best_method"]
        if wanted not in model["scores"]:
            wanted = metrics["best_method"]
        return 200, {
            "user": user_index,
            "method": wanted,
            "recommendations": _recommendations(data, model, wanted, user_index),
        }

    if method == "POST" and path == "/api/train":
        seed = _number(payload, "seed", 42)
        _CACHE.pop(seed, None)
        state = summary()
        return 200, {"retrained": True, "summary": state}

    return 404, {"error": "not found"}
