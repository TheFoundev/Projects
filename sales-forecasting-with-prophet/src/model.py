"""Additive forecast: linear trend + weekly means + yearly sine terms."""
import numpy as np


def fit(data):
    train = data["train"]
    y = train["sales"].to_numpy()
    x = train["day"].to_numpy()
    slope, intercept = np.polyfit(x, y, 1)
    trend = intercept + slope * x
    detrended = y - trend

    weekday_effect = np.array([detrended[train["weekday"].to_numpy() == day].mean() for day in range(7)])
    weekday_effect -= weekday_effect.mean()

    residual = detrended - weekend_effect_lookup(train["weekday"].to_numpy(), weekday_effect)
    design = np.column_stack([
        np.sin(2 * np.pi * x / 365),
        np.cos(2 * np.pi * x / 365),
        np.sin(4 * np.pi * x / 365),
        np.cos(4 * np.pi * x / 365),
    ])
    coefficients, *_ = np.linalg.lstsq(design, residual, rcond=None)
    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "weekday_effect": weekday_effect,
        "yearly_coefficients": coefficients,
    }


def weekend_effect_lookup(weekdays, effects):
    return effects[weekdays]


def predict(model, days):
    days = np.asarray(days)
    trend = model["intercept"] + model["slope"] * days
    weekly = model["weekday_effect"][(days % 7).astype(int)]
    design = np.column_stack([
        np.sin(2 * np.pi * days / 365),
        np.cos(2 * np.pi * days / 365),
        np.sin(4 * np.pi * days / 365),
        np.cos(4 * np.pi * days / 365),
    ])
    return trend + weekly + design @ model["yearly_coefficients"]


def train(data, quick=False):
    model = fit(data)
    days = data["test"]["day"].to_numpy()
    actual = data["test"]["sales"].to_numpy()
    forecast = predict(model, days)
    mae = float(np.mean(np.abs(actual - forecast)))
    mape = float(np.mean(np.abs((actual - forecast) / actual)) * 100)
    return model, {
        "mae": round(mae, 3),
        "mape": round(mape, 3),
        "horizon_days": int(len(days)),
        "training_days": int(len(data["train"])),
    }


def demo(data):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from pathlib import Path

    model, metrics = train(data, quick=True)
    future_days = np.arange(0, 60)
    forecast = predict(model, future_days)
    print(f"Holdout MAE: {metrics['mae']:.2f}, MAPE: {metrics['mape']:.2f}%")
    print(f"Next 7 days: {[round(float(value), 1) for value in forecast[:7]]}")

    Path("artifacts").mkdir(exist_ok=True)
    fig, axis = plt.subplots(figsize=(9, 3.8))
    axis.plot(data["train"]["day"], data["train"]["sales"], label="history", color="#64748b")
    axis.plot(data["test"]["day"], data["test"]["sales"], label="actual", color="#0f172a")
    axis.plot(data["test"]["day"], predict(model, data["test"]["day"].to_numpy()), label="forecast", color="#ea580c")
    axis.legend()
    axis.set_title("Sales forecast")
    fig.tight_layout()
    fig.savefig("artifacts/sales_forecast.png", dpi=110)
    plt.close(fig)
