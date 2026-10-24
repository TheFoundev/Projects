"""The API of the project: the quality of the upscaler and the pictures.

The numbers come from the real core of the project: `src.model.train` searches
the sharpening strength on the validation images and `src.model.evaluate`
measures the PSNR and the mean absolute error of every pair.
"""

from __future__ import annotations

import base64
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from src.data import downsample, load_data, make_image  # noqa: E402
from src.model import evaluate, psnr, train, upscale  # noqa: E402

#: The model, the data and the metrics of the last run.
_STATE: dict = {}


def state() -> dict:
    """Search the sharpening strength once for the process."""
    if "model" not in _STATE:
        data = load_data(seed=42, quick=False)
        model, metrics = train(data, quick=False)
        _STATE["data"] = data
        _STATE["model"] = model
        _STATE["metrics"] = metrics
    return _STATE


def image_rows() -> list:
    """The score of every image of the validation set."""
    current = state()
    model = current["model"]
    rows = []
    for index, pair in enumerate(current["data"]["pairs"]):
        score, error = evaluate([pair], radius=model["radius"], percent=model["percent"])
        rows.append({
            "image": f"image {index + 1}",
            "psnr": round(float(score), 2),
            "mae": round(float(error), 3),
        })
    return rows


def png_base64(array: np.ndarray) -> str:
    """An RGB array as a PNG data URL."""
    buffer = io.BytesIO()
    Image.fromarray(array.astype("uint8")).save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def summary() -> dict:
    """The state of the upscaler: the PSNR, the error and the sharpening."""
    current = state()
    metrics = current["metrics"]
    model = current["model"]
    rows = image_rows()
    return {
        "stats": {
            "psnr": metrics["psnr"],
            "mae": metrics["mae"],
            "percent": model["percent"],
            "validation_images": metrics["validation_images"],
        },
        "series": [
            {"label": row["image"], "value": row["psnr"]} for row in rows
        ],
        "lists": {
            "images": rows,
        },
    }


def handle(method, path, payload, user):
    """The read and the write endpoints of the project."""
    if method == "GET" and path == "/api/images":
        return 200, {"images": image_rows()}
    if method == "POST" and path == "/api/upscale":
        current = state()
        model = current["model"]
        high = make_image(4242, 64)
        low = downsample(high, 4)
        output = upscale(low, radius=model["radius"], percent=model["percent"])
        height = min(output.shape[0], high.shape[0])
        width = min(output.shape[1], high.shape[1])
        return 200, {
            "image": png_base64(output),
            "input": f"{low.shape[1]}x{low.shape[0]}",
            "output": f"{output.shape[1]}x{output.shape[0]}",
            "psnr": round(float(psnr(high[:height, :width], output[:height, :width])), 2),
            "sharpening": model["percent"],
        }
    if method == "POST" and path == "/api/train":
        data = load_data(seed=42, quick=False)
        model, metrics = train(data, quick=False)
        _STATE["data"], _STATE["model"], _STATE["metrics"] = data, model, metrics
        return 200, metrics
    return 404, {"error": "not found"}
