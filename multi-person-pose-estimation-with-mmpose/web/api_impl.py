"""The API of the pose estimator.

The estimator of the project is used as it is: the bright pixels of a frame
are grouped in two people, the joints are read off the bounding box of every
person and the accuracy is the PCK of the joints against the truth of the
synthetic scene.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from src.data import JOINT_NAMES, load_data  # noqa: E402
from src.model import estimate, pck, train  # noqa: E402

#: The thresholds the project searches through, and the fitted state.
THRESHOLDS = (100, 120, 140, 160)
_CACHE: dict[int, tuple] = {}


def _state(seed: int = 42):
    """The scenes, the fitted threshold and the metrics of the run."""
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


def _threshold_scores(data) -> list[dict]:
    """The PCK of every threshold the project tries."""
    rows = []
    for threshold in THRESHOLDS:
        scores = []
        for scene in data["scenes"]:
            predicted = estimate(scene["image"], threshold)
            value, _ = pck(predicted, scene["joints"], size=scene["image"].shape[0])
            scores.append(value)
        rows.append({"threshold": threshold, "pck": round(float(np.mean(scores)), 4)})
    return rows


def _joints(data, model, scene_index: int = 0) -> list[dict]:
    """The estimated joints of one scene, next to the true ones."""
    scene = data["scenes"][scene_index]
    predicted = estimate(scene["image"], model["threshold"])
    rows = []
    for person_index, person in enumerate(predicted):
        truth = scene["joints"][person_index] if person_index < len(scene["joints"]) else None
        for joint_index, name in enumerate(JOINT_NAMES):
            point = person[joint_index]
            rows.append({
                "person": person_index + 1,
                "joint": name,
                "x": round(float(point[0]), 1),
                "y": round(float(point[1]), 1),
                "true_x": round(float(truth[joint_index][0]), 1) if truth is not None else "",
                "true_y": round(float(truth[joint_index][1]), 1) if truth is not None else "",
            })
    return rows


def summary():
    data, model, metrics = _state()
    return {
        "stats": {
            "pck": metrics["pck"],
            "threshold": metrics["threshold"],
            "joints": metrics["joints_evaluated"],
            "people": metrics["people"],
        },
        "series": [{"label": f"threshold {row['threshold']}", "value": row["pck"]}
                   for row in _threshold_scores(data)],
        "lists": {
            "poses": _joints(data, model),
            "scenes": [
                {"scene": index + 1, "people": len(scene["joints"]),
                 "size": int(scene["image"].shape[0])}
                for index, scene in enumerate(data["scenes"])
            ],
        },
    }


def handle(method, path, payload, user):
    if method == "GET" and path == "/api/poses":
        seed = _number(payload, "seed", 42)
        scene = _number(payload, "scene", 0)
        data, model, _ = _state(seed)
        return 200, {"scene": scene, "joints": _joints(data, model, scene)}

    if method == "POST" and path == "/api/train":
        seed = _number(payload, "seed", 42)
        _CACHE.pop(seed, None)
        state = summary()
        return 200, {"retrained": True, "summary": state}

    return 404, {"error": "not found"}
