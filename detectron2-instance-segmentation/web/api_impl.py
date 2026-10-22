"""The API of the project: the masks of the samples and the threshold sweep.

The numbers come from a real run of the segmentation: the images are
thresholded, the connected components become the instances and every mask is
matched with the truth by the IoU.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data import load_data  # noqa: E402
from src.model import evaluate, mask_iou, segment, train  # noqa: E402

#: The thresholds the training sweeps.
THRESHOLDS = (90, 100, 110, 120, 130)

#: The model, the metrics and the samples of the last run.
_STATE: dict = {}


def state() -> dict:
    """Sweep the threshold and measure the masks, once for the process."""
    if "model" not in _STATE:
        data = load_data(seed=42, quick=False)
        model, metrics = train(data, quick=False)
        _STATE["data"] = data
        _STATE["model"] = model
        _STATE["metrics"] = metrics
    return _STATE


def samples() -> list:
    """Every sample with the instances of the truth and the ones that were found."""
    current = state()
    threshold = current["model"]["threshold"]
    rows = []
    for index, sample in enumerate(current["data"]["samples"], start=1):
        instances = segment(sample["image"], threshold)
        truth = sample["masks"]
        best = [
            max((mask_iou(target, predicted) for predicted in instances), default=0.0)
            for target in truth
        ]
        rows.append({
            "sample": index,
            "truth": len(truth),
            "found": len(instances),
            "best_iou": round(sum(best) / len(best), 4) if best else 0.0,
        })
    return rows


def thresholds() -> list:
    """The sweep of the threshold with the mean IoU of every threshold."""
    current = state()
    rows = []
    for threshold in THRESHOLDS:
        metrics = evaluate(current["data"]["samples"], threshold)
        rows.append({
            "threshold": threshold,
            "mean_iou": metrics["mean_iou"],
            "count_error": metrics["count_error"],
        })
    return rows


def summary() -> dict:
    """The state of the last run: the mean IoU and the threshold that was kept."""
    current = state()
    metrics = current["metrics"]
    sweep = thresholds()
    return {
        "stats": {
            "mean_iou": metrics["mean_iou"],
            "count_error": metrics["count_error"],
            "instances": metrics["instances"],
            "threshold": current["model"]["threshold"],
        },
        "series": [
            {"label": str(row["threshold"]), "value": row["mean_iou"]} for row in sweep
        ],
        "lists": {
            "samples": samples(),
            "thresholds": sweep,
        },
    }


def handle(method, path, payload, user):
    """The read and the write endpoints of the project."""
    if method == "GET" and path == "/api/samples":
        return 200, {"samples": samples()}
    if method == "GET" and path == "/api/thresholds":
        return 200, {"thresholds": thresholds()}
    if method == "POST" and path == "/api/evaluate":
        data = load_data(seed=42, quick=False)
        model, metrics = train(data, quick=False)
        _STATE["data"], _STATE["model"], _STATE["metrics"] = data, model, metrics
        return 200, metrics
    return 404, {"error": "not found"}
