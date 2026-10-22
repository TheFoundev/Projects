"""The API of the sales forecast.

The numbers are the real ones: the sales series is built by the project, the
model is fitted on its training days by the project and the forecast, the
error and the effect of the days of the week come out of that fit. Nothing is
stored and nothing is faked; the model is fitted in the process that answers
the request and kept until it is fitted again.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from src.data import load_data  # noqa: E402
from src.model import fit, predict, train  # noqa: E402

#: The fitted model of every seed, so a page does not fit it again for every call.
_CACHE: dict[int, tuple] = {}

#: The names of the days of the week, the first day of the series is a Monday.
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _state(seed: int = 42):
    """The data, the fitted model and the metrics of the run."""
    if seed not in _CACHE:
        data = load_data(seed=seed)
        model, metrics = train(data)
        _CACHE[seed] = (data, model, metrics)
    return _CACHE[seed]


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


def _future(data, model, days: int = 7) -> list[dict]:
    """The forecast of the days that follow the series."""
    last = int(data["full"]["day"].to_numpy()[-1])
    numbers = np.arange(last + 1, last + 1 + days)
    values = predict(model, numbers)
    return [
        {
            "day": int(number),
            "weekday": WEEKDAYS[int(number) % 7],
            "forecast": round(float(value), 1),
        }
        for number, value in zip(numbers, values)
    ]


def _weekdays(model) -> list[dict]:
    """The effect of every day of the week."""
    return [
        {"day": WEEKDAYS[index], "effect": round(float(effect), 2)}
        for index, effect in enumerate(model["weekday_effect"])
    ]


def summary():
    data, model, metrics = _state()

    return {
        "stats": {
            "mae": metrics["mae"],
            "mape": metrics["mape"],
            "horizon_days": metrics["horizon_days"],
            "training_days": metrics["training_days"],
        },
        "series": [
            {"label": row["weekday"], "value": row["forecast"]}
            for row in _future(data, model, 7)
        ],
        "lists": {
            "forecast": _future(data, model, 7),
            "weekdays": _weekdays(model),
        },
    }


def handle(method, path, payload, user):
    if method == "GET" and path == "/api/forecast":
        seed = _number(payload, "seed", 42)
        days = _number(payload, "days", 7)
        data, model, _metrics = _state(seed)
        return 200, {"forecast": _future(data, model, max(1, min(days, 60)))}

    if method == "GET" and path == "/api/weekdays":
        _data, model, _metrics = _state()
        return 200, {"weekdays": _weekdays(model)}

    if method == "POST" and path == "/api/train":
        seed = _number(payload, "seed", 42)
        _CACHE.pop(seed, None)
        state = summary()
        return 200, {"retrained": True, "summary": state}

    return 404, {"error": "not found"}
