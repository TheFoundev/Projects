"""The domain logic behind the API of the medical imaging demo.

The volume is really built, the segmenter really runs on it and the Dice
coefficient of the segmentation really measured.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.data import load_data  # noqa: E402
from src.model import dice, segment, train, volume_features  # noqa: E402

_STATE = {}


def _run():
    if "result" not in _STATE:
        data = load_data(seed=42, quick=True)
        # The percentile of the segmenter is the one the project really
        # selects on the training set.
        _model_info, metrics = train(data, quick=True)
        percentile = metrics["threshold_percentile"]
        # A volume that really carries a lesion, so the Dice of the panel
        # is the Dice of a segmentation and not of an empty volume.
        volume, truth, _label = next(
            (item for item in data["test"] if item[1].any()), data["sample"]
        )
        predicted = segment(volume, percentile)
        _STATE["result"] = {
            "volume": volume,
            "truth": truth,
            "predicted": predicted,
            "dice": dice(predicted, truth),
            "metrics": metrics,
        }
    return _STATE["result"]


def summary():
    result = _run()
    raw = volume_features(result["volume"], result["predicted"])
    features = {"foreground voxels": raw[0], "mean intensity": raw[1], "std intensity": raw[2]}
    return {
        "stats": {
            "dice": round(result["dice"], 4),
            "mean_dice": result["metrics"]["mean_dice"],
            "accuracy": result["metrics"]["classification_accuracy"],
            "percentile": result["metrics"]["threshold_percentile"],
        },
        "series": [
            {"label": name, "value": round(float(value), 4)} for name, value in features.items()
        ],
        "lists": {
            "features": [
                {"feature": name, "value": round(float(value), 4)} for name, value in features.items()
            ]
        },
    }


def handle(method, path, payload, user):
    if method == "GET" and path.endswith("/features"):
        return 200, {"features": summary()["lists"]["features"]}
    return 404, {"error": "not found"}
