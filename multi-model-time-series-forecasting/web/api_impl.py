"""The API of the forecasting benchmark.

Every number comes from the project's own baselines: the series is built, the
forecasts of the holdout are made by the seasonal naive, the moving average,
the linear trend, the seasonal trend and SARIMAX, and they are scored with the
mean absolute error and the root mean squared error of the project.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.data import load_data  # noqa: E402
from src.model import (  # noqa: E402
    linear_trend,
    moving_average,
    rolling_origin_evaluation,
    score,
    seasonal_naive,
    seasonal_naive_with_trend,
    train,
)

#: The fitted state of the benchmark, kept between the calls.
_CACHE: dict[int, tuple] = {}


def _state(seed: int = 42):
    """The data, the forecasts and the metrics of the run."""
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


def _scores(data, model) -> list[dict]:
    """The error of every baseline on the holdout."""
    actual = data["test"]["value"].to_numpy()
    rows = []
    for name, prediction in model["forecasts"].items():
        mae, rmse = score(actual, prediction)
        rows.append({"model": name, "mae": round(float(mae), 3), "rmse": round(float(rmse), 3)})
    rows.sort(key=lambda row: row["mae"])
    return rows


def summary():
    data, model, metrics = _state()
    rows = _scores(data, model)

    # The days of the holdout with the forecast of the best model and what
    # really happened, so the console shows the error and not only the score.
    actual = data["test"]["value"].to_numpy()
    best = model["forecasts"][model["method"]][: len(actual)]
    days = data["test"]["day"].tolist()
    timeline = [
        {"day": int(day), "actual": round(float(value), 2), "forecast": round(float(prediction), 2)}
        for day, value, prediction in zip(days, actual, best)
    ][:12]

    return {
        "stats": {
            "best_mae": metrics["best_mae"],
            "best_rmse": metrics["best_rmse"],
            "models": metrics["models_compared"],
            "holdout": metrics["holdout_days"],
        },
        "series": [{"label": row["model"], "value": row["mae"]} for row in rows],
        "lists": {
            "models": rows,
            "timeline": timeline,
        },
    }


def handle(method, path, payload, user):
    if method == "GET" and path == "/api/forecasts":
        data, model, _ = _state(_number(payload, "seed", 42))
        return 200, {"method": model["method"], "models": _scores(data, model)}

    if method == "POST" and path == "/api/train":
        seed = _number(payload, "seed", 42)
        _CACHE.pop(seed, None)
        state = summary()
        return 200, {"retrained": True, "summary": state}

    if method == "POST" and path == "/api/rolling":
        # The same baselines, measured over several windows of the history
        # instead of one single split.
        seed = _number(payload, "seed", 42)
        data = load_data(seed=seed)
        folds = _number(payload, "folds", 3)
        models = {
            "seasonal_naive": seasonal_naive,
            "moving_average": moving_average,
            "linear_trend": linear_trend,
            "seasonal_trend": seasonal_naive_with_trend,
        }
        results = rolling_origin_evaluation(data, models, folds=folds, horizon=7)
        return 200, {"folds": folds, "mean_absolute_error": results}

    return 404, {"error": "not found"}
