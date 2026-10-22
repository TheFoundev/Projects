"""The API of the object detector.

The numbers are the real ones: the scenes are made by the project, the
classifier is fitted on the crops of the project and the proposals come out
of the connected bright regions of the pictures. The precision and the recall
of the boxes are measured against the true boxes of the scenes, so the console
shows what the detector really finds.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.data import load_data  # noqa: E402
from src.model import box_iou, proposal_boxes, train  # noqa: E402

#: The scenes, the classifier and the metrics of every seed.
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
    """The scenes, the trained classifier and the metrics of the run."""
    if seed not in _CACHE:
        data = load_data(seed=seed)
        model, metrics = train(data)
        _CACHE[seed] = (data, model, metrics)
    return _CACHE[seed]


def _scenes(data) -> list[dict]:
    """The proposals and the true boxes of every scene of the set."""
    rows = []
    for index, scene in enumerate(data["scenes"]):
        proposals = proposal_boxes(scene["image"])
        hits = 0
        matched = set()
        for truth in scene["boxes"]:
            best = 0.0
            best_index = -1
            for position, proposal in enumerate(proposals):
                if position in matched:
                    continue
                overlap = box_iou(truth, proposal)
                if overlap > best:
                    best = overlap
                    best_index = position
            if best >= 0.4:
                hits += 1
                matched.add(best_index)
        rows.append({
            "picture": index + 1,
            "proposals": len(proposals),
            "true boxes": len(scene["boxes"]),
            "hits": hits,
        })
    return rows


def summary():
    data, _model, metrics = _state()
    rows = _scenes(data)

    return {
        "stats": {
            "class_accuracy": metrics["class_accuracy"],
            "box_precision": metrics["box_precision"],
            "box_recall": metrics["box_recall"],
            "crops": metrics["crops"],
        },
        "series": [
            {"label": f"picture {row['picture']}", "value": row["proposals"]}
            for row in rows
        ],
        "lists": {
            "scenes": rows,
        },
    }


def handle(method, path, payload, user):
    if method == "GET" and path == "/api/scenes":
        data, _model, _metrics = _state()
        return 200, {"scenes": _scenes(data)}

    if method == "POST" and path == "/api/train":
        seed = _number(payload, "seed", 42)
        _CACHE.pop(seed, None)
        state = summary()
        return 200, {"retrained": True, "summary": state}

    return 404, {"error": "not found"}
