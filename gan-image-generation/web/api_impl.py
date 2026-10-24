"""The API of the project: the losses of the training and the samples.

The numbers come from the real core of the project: `src.model.train` fits
the generator and the discriminator of `src/model.py` against each other and
returns the two losses of the last step. A sample is drawn with the
generator that was fitted, and the grid is the file the training wrote.
"""

from __future__ import annotations

import base64
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from src.data import load_data  # noqa: E402
from src.model import train  # noqa: E402

#: The generator, the metrics and the data of the last run.
_STATE: dict = {}


def state() -> dict:
    """Train the pair once for the process."""
    if "model" not in _STATE:
        data = load_data(seed=42, quick=False)
        model, metrics = train(data, quick=False)
        _STATE["data"] = data
        _STATE["model"] = model
        _STATE["metrics"] = metrics
    return _STATE


def png_base64(path: Path) -> str:
    """A picture of the project as a data URL."""
    if not path.is_file():
        return ""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def generate() -> str:
    """Draw one sample with the generator that was fitted."""
    current = state()
    generator = current["model"]
    noise = np.random.default_rng(7).normal(0, 1, (1, 12)).astype("float32")
    image = np.asarray(generator.predict(noise, verbose=0))[0, :, :, 0]
    return _image_to_png(image)


def _image_to_png(image: np.ndarray) -> str:
    """A grey-scale array as a PNG data URL."""
    import io

    from PIL import Image

    scaled = np.clip((image + 1.0) * 127.5, 0, 255).astype("uint8")
    buffer = io.BytesIO()
    Image.fromarray(scaled, mode="L").save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def summary() -> dict:
    """The state of the training: the two losses, the steps and the dataset."""
    current = state()
    metrics = current["metrics"]
    grid = ROOT / "artifacts" / "gan_samples.png"
    return {
        "stats": {
            "generator_loss": metrics["generator_loss"],
            "discriminator_loss": metrics["discriminator_loss"],
            "steps": metrics["steps"],
            "training_images": metrics["training_images"],
        },
        "series": [
            {"label": "Generator loss", "value": metrics["generator_loss"]},
            {"label": "Discriminator loss", "value": metrics["discriminator_loss"]},
            {"label": "Training steps", "value": metrics["steps"]},
            {"label": "Training images", "value": metrics["training_images"]},
        ],
        "lists": {
            "samples": [
                {
                    "artefact": "artifacts/gan_samples.png",
                    "written": "yes" if grid.is_file() else "no",
                    "steps": metrics["steps"],
                    "images": metrics["training_images"],
                }
            ],
        },
    }


def handle(method, path, payload, user):
    """The read and the write endpoints of the project."""
    if method == "GET" and path == "/api/samples":
        grid = ROOT / "artifacts" / "gan_samples.png"
        return 200, {
            "artefact": "artifacts/gan_samples.png",
            "exists": grid.is_file(),
            "image": png_base64(grid),
        }
    if method == "GET" and path == "/api/grid":
        grid = ROOT / "artifacts" / "gan_samples.png"
        if not grid.is_file():
            return 200, {"image": "", "error": "no grid yet: run the training first"}
        return 200, {"image": png_base64(grid), "artefact": "artifacts/gan_samples.png"}
    if method == "POST" and path == "/api/generate":
        return 200, {"image": generate(), "artefact": "drawn with the fitted generator"}
    if method == "POST" and path == "/api/train":
        data = load_data(seed=42, quick=False)
        model, metrics = train(data, quick=False)
        _STATE["data"], _STATE["model"], _STATE["metrics"] = data, model, metrics
        return 200, metrics
    return 404, {"error": "not found"}
