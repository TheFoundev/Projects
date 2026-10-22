"""The API of the project: the metrics of the detector and the scenes.

The numbers come from the real perception code of the project: the lane
threshold is fitted on one part of the scenes and the metrics are measured on
the other part, so the numbers the console shows are the ones of a real run.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data import load_data  # noqa: E402
from src.model import (  # noqa: E402
    LANE_THRESHOLDS,
    detect_vehicles,
    evaluate,
    lane_iou,
    split_scenes,
    train,
)

#: The model, the metrics and the scenes of the last run.
_STATE: dict = {}


def state() -> dict:
    """Fit the threshold and measure the detector, once for the process."""
    if "model" not in _STATE:
        data = load_data(seed=42, quick=False)
        model, metrics = train(data, quick=False)
        _STATE["data"] = data
        _STATE["model"] = model
        _STATE["metrics"] = metrics
    return _STATE


def scenes() -> list:
    """Every scene of the test set with its lane IoU and its vehicles."""
    current = state()
    _, testing = split_scenes(current["data"])
    model = current["model"]
    rows = []
    for index, scene in enumerate(testing, start=1):
        predicted = scene["image"] > model["lane_threshold"]
        found = detect_vehicles(scene["image"], threshold=model["vehicle_threshold"])
        rows.append({
            "scene": index,
            "lane_iou": round(lane_iou(predicted, scene["lane_mask"]), 4),
            "found": len(found),
            "truth": len(scene["boxes"]),
        })
    return rows


def thresholds() -> list:
    """The sweep of the lane threshold over the scenes it is fitted on."""
    current = state()
    tuning, _ = split_scenes(current["data"])
    rows = []
    for threshold in LANE_THRESHOLDS:
        metrics = evaluate(tuning, lane_threshold=threshold)
        rows.append({
            "threshold": threshold,
            "lane_iou": metrics["lane_iou"],
            "precision": metrics["vehicle_precision"],
            "recall": metrics["vehicle_recall"],
        })
    return rows


def summary() -> dict:
    """The state of the detector: the lane IoU and the vehicles."""
    current = state()
    metrics = current["metrics"]
    sweep = thresholds()
    return {
        "stats": {
            "lane_iou": metrics["lane_iou"],
            "vehicle_precision": metrics["vehicle_precision"],
            "vehicle_recall": metrics["vehicle_recall"],
            "scenes": metrics["test_scenes"],
        },
        "series": [
            {"label": str(row["threshold"]), "value": row["lane_iou"]} for row in sweep
        ],
        "lists": {
            "scenes": scenes(),
            "thresholds": sweep,
        },
    }


def handle(method, path, payload, user):
    """The read and the write endpoints of the project."""
    if method == "GET" and path == "/api/scenes":
        return 200, {"scenes": scenes()}
    if method == "GET" and path == "/api/thresholds":
        return 200, {"thresholds": thresholds()}
    if method == "POST" and path == "/api/evaluate":
        data = load_data(seed=42, quick=False)
        model, metrics = train(data, quick=False)
        _STATE["data"], _STATE["model"], _STATE["metrics"] = data, model, metrics
        return 200, metrics
    return 404, {"error": "not found"}
