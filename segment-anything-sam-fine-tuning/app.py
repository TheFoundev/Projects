"""Promptable segmentation over a small HTTP API.

The endpoint of the project is `POST /segment`: it answers with the mask of
the object a prompt points at. The home page of the site of the project, its
console and the JSON API live in `web/` and are served by this same
application.
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.data import load_data, make_sample
from src.model import decode, encode_image, encode_mask, iou, train

app = FastAPI(title="Promptable segmentation demo")
THRESHOLD = 110
BIAS = 0

WEB = Path(__file__).resolve().parent / "web"

#: The model of the project, fitted on its own pictures.
DATA = load_data(seed=42, quick=True)
MODEL, METRICS = train(DATA, quick=True)


class Prompt(BaseModel):
    """A prompt: a point, a box or a mask."""

    x: int | None = None
    y: int | None = None
    box: list[int] | None = None
    mask: list[list[bool]] | None = None
    seed: int = 1


@app.get("/")
def root():
    """The home page of the site of the project."""
    return FileResponse(WEB / "index.html")


@app.get("/console.html")
def console():
    """The console of the site of the project."""
    return FileResponse(WEB / "console.html")


@app.get("/api/info")
def info():
    """What the service is and which prompts it takes."""
    return {
        "service": "promptable-segmentation",
        "method": "encoder + decoder with a point, a box or a mask",
        "prompts": ["point", "box", "mask"],
    }


@app.post("/segment")
def run_prompt(prompt: Prompt):
    sample = make_sample(seed=prompt.seed)
    embedding = encode_image(sample["image"], THRESHOLD)

    if prompt.box is not None:
        request = {"box": prompt.box}
    elif prompt.mask is not None:
        request = {"mask": prompt.mask}
    elif prompt.x is not None and prompt.y is not None:
        request = {"point": (prompt.x, prompt.y)}
    else:
        return {"error": "a point, a box or a mask is needed"}

    mask = decode(embedding, request, BIAS)
    ys, xs = (mask.nonzero() if mask.any() else ([], []))

    return {
        "pixels": int(mask.sum()),
        "bbox": [int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))] if mask.any() else None,
        "image_size": list(sample["image"].shape),
        "rle": encode_mask(mask),
        "iou_with_the_truth": round(iou(mask, sample["mask"]), 4),
    }


# ------------------------------------------------------------------ #
# The web layer of the project                                        #
# ------------------------------------------------------------------ #

@app.get("/api/summary")
def api_summary():
    """The metrics of the model and the answer for every picture of the set."""
    rows = _predictions(DATA, MODEL)
    return {
        "stats": {
            "mean_iou": METRICS["mean_iou"],
            "loss": METRICS["loss"],
            "threshold": METRICS["threshold"],
            "bias": METRICS["bias"],
        },
        "series": [
            {"label": f"picture {row['picture']}", "value": row["iou"]}
            for row in rows
        ],
        "lists": {
            "predictions": rows,
            "history": [
                {"round": index + 1, "loss": loss}
                for index, loss in enumerate(METRICS["history"])
            ],
        },
    }


@app.get("/api/predictions")
def api_predictions():
    """The answer for every picture of the set."""
    return {"predictions": _predictions(DATA, MODEL)}


@app.post("/api/train")
def api_train():
    """Fine tune the decoder again and answer with the new metrics."""
    global DATA, MODEL, METRICS
    DATA = load_data(seed=42, quick=True)
    MODEL, METRICS = train(DATA, quick=True)
    return {"retrained": True, "metrics": METRICS, "summary": api_summary()}


def _predictions(data, model) -> list[dict]:
    """The mask of every picture of the set, with the overlap with the truth."""
    rows = []
    for index, sample in enumerate(data["samples"]):
        embedding = encode_image(sample["image"], model["threshold"])
        mask = decode(embedding, {"point": sample["point"]}, model["bias"])
        rows.append({
            "picture": index + 1,
            "prompt point": f"{sample['point'][0]}, {sample['point'][1]}",
            "pixels": int(mask.sum()),
            "iou": round(iou(mask, sample["mask"]), 4),
        })
    return rows


app.mount("/assets", StaticFiles(directory=str(WEB / "assets")), name="assets")


if __name__ == "__main__":
    import os

    import uvicorn

    uvicorn.run(app, host=os.environ.get("HOST", "127.0.0.1"),
                port=int(os.environ.get("PORT", "5000")))
