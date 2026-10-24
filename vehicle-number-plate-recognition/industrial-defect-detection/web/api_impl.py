"""The API of the project: the scores of the detector and the verdict.

The numbers come from the real core of the project: `src.model.train` fits
the PCA on the clean patches and returns the threshold, and
`src.model.reconstruction_scores` scores every patch of the test set with
that very model.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from src.data import load_data, make_patch  # noqa: E402
from src.model import reconstruction_scores, train  # noqa: E402

#: The model, the data and the metrics of the last run.
_STATE: dict = {}


def state() -> dict:
    """Fit the detector once for the process."""
    if "model" not in _STATE:
        data = load_data(seed=42, quick=False)
        model, metrics = train(data, quick=False)
        _STATE["data"] = data
        _STATE["model"] = model
        _STATE["metrics"] = metrics
    return _STATE


def score_rows() -> list:
    """The anomaly score of every patch of the test set."""
    current = state()
    data = current["data"]
    scores = reconstruction_scores(current["model"]["pca"], data["X_test"])
    threshold = current["model"]["threshold"]
    rows = []
    for index, score in enumerate(scores):
        label = int(data["y_test"][index])
        rows.append({
            "patch": f"patch {index + 1}",
            "score": round(float(score), 6),
            "label": "defect" if label else "clean",
            "verdict": "defect" if float(score) > threshold else "clean",
        })
    return rows


def summary() -> dict:
    """The state of the detector: the AUC, the precision, the recall."""
    current = state()
    metrics = current["metrics"]
    rows = score_rows()
    return {
        "stats": {
            "roc_auc": metrics["roc_auc"],
            "precision": metrics["precision"],
            "recall": metrics["recall"],
            "test_patches": metrics["test_patches"],
        },
        "series": [
            {"label": row["patch"], "value": row["score"]} for row in rows
        ],
        "lists": {
            "scores": rows,
        },
    }


def handle(method, path, payload, user):
    """The read and the write endpoints of the project."""
    if method == "GET" and path == "/api/scores":
        return 200, {"scores": score_rows(), "threshold": state()["model"]["threshold"]}
    if method == "POST" and path == "/api/scan":
        current = state()
        threshold = current["model"]["threshold"]
        seed = int(np.random.randint(0, 100000))
        defective = bool(np.random.random() < 0.5)
        patch, mask, label = make_patch(seed, 40, defective)
        score = float(reconstruction_scores(current["model"]["pca"], patch[None, ...])[0])
        return 200, {
            "seed": seed,
            "score": round(score, 6),
            "threshold": round(float(threshold), 6),
            "verdict": "defect" if score > threshold else "clean",
            "truly_defective": "yes" if label else "no",
            "defect_pixels": int(mask.sum()),
        }
    if method == "POST" and path == "/api/train":
        data = load_data(seed=42, quick=False)
        model, metrics = train(data, quick=False)
        _STATE["data"], _STATE["model"], _STATE["metrics"] = data, model, metrics
        return 200, metrics
    return 404, {"error": "not found"}
