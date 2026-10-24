"""The API of the semantic segmentation.

The numbers are the real ones: the pictures are made by the project, the tiny
U-Net is built and fitted by the project and the dice and the pixel accuracy
come out of the prediction of the network on the pictures it did not see.

The training runs as the entry point of the project does, in a process of its
own: `web/train_run.py` calls `src.model.train` of the project, prints the
metrics of the run and writes the fitted network to `artifacts/model.keras`.
The run happens in its own process because TensorFlow seeds its operations
with the thread that creates them, and a network that is fitted in the thread
of an HTTP request comes out dead.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

#: The marker that says where the answer of the training run starts.
MARKER = "###RUN###"

#: The metrics and the predictions of the last training run.
_CACHE: dict[str, dict] = {}


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


def _train(seed: int = 42) -> dict:
    """The real training run of the project, in a process of its own."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "web" / "train_run.py")],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=1800,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip()[-400:] or "the training failed")
    if MARKER not in result.stdout:
        raise RuntimeError("the training printed no metrics")
    return json.loads(result.stdout.split(MARKER, 1)[1])


def _state(seed: int = 42) -> dict:
    """The training run of the seed, done once and kept."""
    key = str(seed)
    if key not in _CACHE:
        _CACHE[key] = _train(seed)
    return _CACHE[key]


def summary():
    state = _state()
    metrics = state["metrics"]
    rows = state["predictions"]

    return {
        "stats": {
            "dice": metrics["dice"],
            "pixel_accuracy": metrics["pixel_accuracy"],
            "test_images": metrics["test_images"],
            "epochs": metrics["epochs"],
        },
        "series": [
            {"label": f"picture {row['picture']}", "value": row["dice"]}
            for row in rows
        ],
        "lists": {
            "predictions": rows,
        },
    }


def handle(method, path, payload, user):
    if method == "GET" and path == "/api/predictions":
        return 200, {"predictions": _state()["predictions"]}

    if method == "POST" and path == "/api/train":
        seed = _number(payload, "seed", 42)
        _CACHE.clear()
        state = summary()
        return 200, {"retrained": True, "summary": state}

    return 404, {"error": "not found"}


# The run is made when the server starts, so the first page of the console
# does not wait for the training.
_state()
