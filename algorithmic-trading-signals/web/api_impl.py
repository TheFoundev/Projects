"""The API of the project: the metrics of the backtest and the daily signals.

The numbers come from the real model of the project: the random forest is
fitted on the first three quarters of the price series and the predictions of
the last quarter are traded in the backtest of `src/model.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data import load_data  # noqa: E402
from src.model import FEATURES, add_features, train  # noqa: E402

#: How many days of the test window the console shows.
RECENT_DAYS = 12

#: The model, the metrics and the data of the last run.
_STATE: dict = {}


def state() -> dict:
    """Fit the model and the backtest, once for the process."""
    if "model" not in _STATE:
        data = load_data(seed=42, quick=False)
        model, metrics = train(data, quick=False)
        _STATE["data"] = data
        _STATE["model"] = model
        _STATE["metrics"] = metrics
    return _STATE


def signals() -> list:
    """The signal of every day of the last stretch of the test window."""
    current = state()
    frame = add_features(current["data"]["test"])
    classifier = current["model"]
    predictions = classifier.predict(frame[FEATURES])
    rows = []
    for index in range(max(0, len(frame) - RECENT_DAYS), len(frame)):
        row = frame.iloc[index]
        rows.append({
            "day": index + 1,
            "close": round(float(row["close"]), 2),
            "rsi": round(float(row["rsi_14"]), 1),
            "model": "up" if predictions[index] == 1 else "down",
            "next_day": "up" if row["target"] == 1 else "down",
        })
    return rows


def features() -> list:
    """The six features the model reads, for the last day of the series."""
    current = state()
    frame = add_features(current["data"]["prices"])
    last = frame.iloc[-1]
    return [
        {"feature": name, "value": round(float(last[name]), 4)} for name in FEATURES
    ]


def summary() -> dict:
    """The state of the backtest: the accuracy, the returns and the signals."""
    current = state()
    metrics = current["metrics"]
    days = signals()
    return {
        "stats": {
            "accuracy": metrics["accuracy"],
            "strategy_return": metrics["strategy_return"],
            "buy_hold_return": metrics["buy_hold_return"],
            "sharpe_like": metrics["sharpe_like"],
        },
        "series": [
            {"label": "day " + str(row["day"]), "value": row["close"]} for row in days
        ],
        "lists": {
            "signals": days,
            "features": features(),
        },
    }


def handle(method, path, payload, user):
    """The read and the write endpoints of the project."""
    if method == "GET" and path == "/api/signals":
        return 200, {"signals": signals()}
    if method == "GET" and path == "/api/features":
        return 200, {"features": features()}
    if method == "POST" and path == "/api/backtest":
        current = state()
        data = load_data(seed=42, quick=False)
        model, metrics = train(data, quick=False)
        current["data"], current["model"], current["metrics"] = data, model, metrics
        return 200, metrics
    return 404, {"error": "not found"}
