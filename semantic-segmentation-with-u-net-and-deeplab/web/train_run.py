"""The training run of the project, in a process of its own.

The network of the project is fitted by `src.model.train` on the pictures of
`src.data`, and the metrics it prints are the metrics of that run. The run
happens in a process of its own, because TensorFlow seeds its operations with
the thread that creates them: a network that is fitted in the thread of an
HTTP request comes out dead, and the dice of the run would be zero.

The seed of the initialisation is fixed here, so the console shows the
numbers of the same run every time instead of the numbers of a lucky draw.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

#: The seed of the initialisation of the network.
SEED = 0

#: The marker that says where the answer of the run starts.
MARKER = "###RUN###"


def run(seed: int = 42) -> dict:
    """Fit the network of the project and measure it on the test set."""
    import tensorflow as tf

    tf.keras.utils.set_random_seed(SEED)

    from src.data import load_data
    from src.model import dice_score, train

    data = load_data(seed=seed, quick=False)
    model, metrics = train(data, quick=False)

    artifacts = ROOT / "artifacts"
    artifacts.mkdir(exist_ok=True)
    try:
        model.save(artifacts / "model.keras")
    except Exception:
        pass

    prediction = model.predict(data["X_test"], verbose=0)
    rows = []
    for index, (truth, painted) in enumerate(zip(data["y_test"], prediction)):
        rows.append({
            "picture": index + 1,
            "dice": round(dice_score(truth, painted), 4),
            "painted": int(np.sum(painted > 0.5)),
            "truth": int(np.sum(truth > 0.5)),
        })
    return {"metrics": metrics, "predictions": rows}


if __name__ == "__main__":
    print(MARKER + json.dumps(run()), flush=True)
