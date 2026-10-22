"""The API of the project: the classifier of the digits and the recognizer.

The numbers come from the real core of the project: the words are generated
by `src.data.synthesize`, the features by `src.data.features` and the forest
by `src.model.train`. The confusion matrix is recomputed from the model that
was fitted, so the recall of every digit is the one of that model.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
from sklearn.metrics import confusion_matrix  # noqa: E402

from src.data import DIGITS, features, load_data, synthesize  # noqa: E402
from src.model import train  # noqa: E402

#: The model, the data and the metrics of the last run.
_STATE: dict = {}


def state() -> dict:
    """Fit the classifier once for the process."""
    if "model" not in _STATE:
        data = load_data(seed=42, quick=False)
        model, metrics = train(data, quick=False)
        _STATE["data"] = data
        _STATE["model"] = model
        _STATE["metrics"] = metrics
    return _STATE


def digits() -> list:
    """The recall of every digit, read from the confusion matrix."""
    current = state()
    data = current["data"]
    predictions = current["model"].predict(data["X_test"])
    matrix = confusion_matrix(data["y_test"], predictions, labels=list(range(len(DIGITS))))
    rows = []
    for index, name in enumerate(DIGITS):
        total = int(matrix[index].sum())
        right = int(matrix[index][index])
        confused = ""
        if total - right:
            wrong = int(np.argmax(matrix[index]))
            confused = DIGITS[wrong]
        rows.append({
            "digit": name,
            "recall": round(right / total, 4) if total else 0.0,
            "right": right,
            "mistaken_for": confused or "-",
        })
    return rows


def summary() -> dict:
    """The state of the classifier: the accuracy, the worst digit, the digits."""
    current = state()
    metrics = current["metrics"]
    return {
        "stats": {
            "accuracy": metrics["accuracy"],
            "worst_digit": metrics["worst_digit"],
            "train_samples": metrics["train_samples"],
            "test_samples": metrics["test_samples"],
        },
        "series": [
            {"label": row["digit"], "value": row["recall"]} for row in digits()
        ],
        "lists": {
            "digits": digits(),
        },
    }


def recognize(word: str) -> dict:
    """Synthesise a word and let the classifier say what it heard."""
    current = state()
    name = str(word or "").strip().lower()
    if name not in DIGITS:
        raise ValueError(f"unknown word {word!r}")
    signal = synthesize(name, seed=999)
    vector = features(signal).reshape(1, -1)
    prediction = current["model"].predict(vector)[0]
    probability = float(np.max(current["model"].predict_proba(vector)[0]))
    return {
        "word": name,
        "heard": DIGITS[int(prediction)],
        "correct": DIGITS[int(prediction)] == name,
        "confidence": round(probability, 4),
        "samples": int(len(signal)),
    }


def handle(method, path, payload, user):
    """The read and the write endpoints of the project."""
    if method == "GET" and path == "/api/digits":
        return 200, {"digits": digits()}
    if method == "POST" and path == "/api/recognize":
        try:
            return 200, recognize(payload.get("word", "seven"))
        except ValueError as error:
            return 400, {"error": str(error)}
    if method == "POST" and path == "/api/train":
        data = load_data(seed=42, quick=False)
        model, metrics = train(data, quick=False)
        _STATE["data"], _STATE["model"], _STATE["metrics"] = data, model, metrics
        return 200, metrics
    return 404, {"error": "not found"}
