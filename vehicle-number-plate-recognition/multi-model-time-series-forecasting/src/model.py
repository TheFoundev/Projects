"""Cheap forecasting baselines with one holdout split."""
import numpy as np


def infer_period(values, max_period=52):
    """The season of a series, worked out from its own shape.

    The period is the one that explains the most of the movement of the
    series, so the week of a daily series is found and not assumed.
    """
    values = np.asarray(values, dtype=float)
    if len(values) < 8:
        return 1
    # The trend is taken off first, so a series that only goes up is not
    # taken for a season.
    index = np.arange(len(values), dtype=float)
    slope, intercept = np.polyfit(index, values, 1)
    residual = values - (slope * index + intercept)

    # A season has to be visible: a series that only goes up has no
    # movement left once the trend is taken off.
    if residual.std() < 0.02 * max(values.std(), 1e-9):
        return 1

    scores = {}
    for period in range(2, min(max_period, len(residual) // 2) + 1):
        # How well the series repeats itself after a period.
        left = residual[:-period]
        right = residual[period:]
        scores[period] = float(np.corrcoef(left, right)[0, 1]) if left.std() > 0 and right.std() > 0 else 0.0

    if not scores:
        return 1

    best = max(scores.values())
    if best < 0.3:
        # There is no season in the series.
        return 1

    # The smallest period that explains the series as well as the best one:
    # a week of a daily series also repeats every fourteen days.
    for period in sorted(scores):
        if scores[period] >= best - 0.05:
            return period
    return 1


def seasonal_naive(train, horizon, period=None):
    """The forecast of the last season.

    The first forecast is the value of the day that is one period before the
    end of the history, so the days keep their place in the week.
    """
    values = train["value"].to_numpy()
    if period is None:
        period = infer_period(values)
    if len(values) == 0:
        return np.zeros(horizon)
    if len(values) < period:
        return np.repeat(values[-1], horizon)
    start = len(values) - period
    return np.array([values[start + (index % period)] for index in range(horizon)])


def moving_average(train, horizon, window=7):
    value = float(train["value"].tail(window).mean())
    return np.full(horizon, value)


def linear_trend(train, horizon):
    y = train["value"].to_numpy()
    x = np.arange(len(y))
    slope, intercept = np.polyfit(x, y, 1)
    return intercept + slope * np.arange(len(y), len(y) + horizon)


def seasonal_naive_with_trend(train, horizon, period=None):
    """The forecast of the last season, with the trend of the season.

    The trend is the difference between the last season and the one before
    it, spread over the days of the season.
    """
    values = train["value"].to_numpy()
    if period is None:
        period = infer_period(values)
    base = seasonal_naive(train, horizon, period)
    if len(values) < 2 * period:
        return base
    trend = float(np.mean(values[-period:]) - np.mean(values[-2 * period:-period]))
    return base + trend * np.arange(1, horizon + 1) / period


def mase(train, forecast, actual, period=7):
    """The mean absolute scaled error.

    The error of the forecast is divided by the error of the naive forecast
    of the same period, so the number can be read whatever the size of the
    series is.
    """
    values = train["value"].to_numpy()
    if len(values) < period + 1 or len(actual) == 0:
        return float("inf")
    naive_error = np.mean(np.abs(values[period:] - values[:-period]))
    if naive_error == 0:
        return float("inf")
    error = np.mean(np.abs(np.asarray(actual) - np.asarray(forecast)))
    return float(error / naive_error)


def rolling_origin_evaluation(data, models, folds=3, horizon=7):
    """The models are measured on a few windows of the history.

    Every window is cut out of the history in turn, so the numbers are not
    the ones of a single lucky split.
    """
    frame = data["train"] if "train" in data else data
    total = len(frame)
    results = {name: [] for name in models}

    for fold in range(folds):
        end = total - fold * horizon
        start = max(0, end - horizon * 6)
        if end <= start:
            break
        history = frame.iloc[start:end]
        truth = frame["value"].to_numpy()[end:end + horizon]
        if len(truth) < horizon:
            continue
        for name, function in models.items():
            forecast = function(history, horizon)
            results[name].append(float(np.mean(np.abs(forecast - truth))))

    return {
        name: (round(float(np.mean(values)), 4) if values else None)
        for name, values in results.items()
    }


def sarimax_forecast(train, horizon):
    from statsmodels.tsa.statespace.sarimax import SARIMAX

    model = SARIMAX(
        train["value"].to_numpy(),
        order=(1, 1, 1),
        seasonal_order=(1, 0, 0, 7),
        enforce_stationarity=False,
        enforce_invertibility=False,
    )
    result = model.fit(disp=False)
    forecast = result.forecast(steps=horizon)
    return np.asarray(forecast)


def score(actual, predicted):
    error = np.asarray(actual, dtype=float) - np.asarray(predicted, dtype=float)
    return float(np.mean(np.abs(error))), float(np.sqrt(np.mean(error ** 2)))


def train(data, quick=False):
    horizon = len(data["test"])
    actual = data["test"]["value"].to_numpy()
    candidates = {
        "moving_average": moving_average(data["train"], horizon),
        "linear_trend": linear_trend(data["train"], horizon),
        "seasonal_naive": seasonal_naive(data["train"], horizon),
        "seasonal_trend": seasonal_naive_with_trend(data["train"], horizon),
    }
    if not quick:
        try:
            candidates["sarimax"] = sarimax_forecast(data["train"], horizon)
        except Exception:
            pass

    scores = {}
    for name, prediction in candidates.items():
        mae, rmse = score(actual, prediction)
        scores[name] = (mae, rmse)
    best = min(scores, key=lambda name: scores[name][0])
    return {"method": best, "forecasts": {name: list(map(float, values)) for name, values in candidates.items()}}, {
        "best_method": best,
        "best_mae": round(scores[best][0], 3),
        "best_rmse": round(scores[best][1], 3),
        "models_compared": len(scores),
        "holdout_days": int(horizon),
    }


def demo(data):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from pathlib import Path

    model, metrics = train(data, quick=True)
    print(f"Best baseline: {metrics['best_method']} (MAE {metrics['best_mae']:.2f})")
    horizon = len(data["test"])
    for name, prediction in model["forecasts"].items():
        mae, rmse = score(data["test"]["value"], prediction)
        print(f"  {name:18s} MAE={mae:6.2f} RMSE={rmse:6.2f}")

    Path("artifacts").mkdir(exist_ok=True)
    fig, axis = plt.subplots(figsize=(8, 3.6))
    axis.plot(data["train"]["day"], data["train"]["value"], label="train", color="#475569")
    axis.plot(data["test"]["day"], data["test"]["value"], label="actual", color="#0f172a")
    best_forecast = model["forecasts"][model["method"]]
    axis.plot(data["test"]["day"], best_forecast[:horizon], label=model["method"], color="#dc2626")
    axis.legend()
    axis.set_title("Forecast holdout")
    fig.tight_layout()
    fig.savefig("artifacts/forecast.png", dpi=110)
    plt.close(fig)
