"""Daily sales with trend, weekly/yearly seasonality and holiday bumps."""
import numpy as np
import pandas as pd


def make_sales(days=420, seed=42):
    rng = np.random.default_rng(seed)
    index = np.arange(days)
    trend = 220 + 0.42 * index
    weekly = 18 * np.sin(2 * np.pi * (index % 7) / 7 + 0.4)
    yearly = 32 * np.sin(2 * np.pi * index / 365 - 0.8)
    holidays = np.zeros(days)
    for center in (40, 150, 270, 390):
        holidays += 55 * np.exp(-((index - center) ** 2) / 8)
    noise = rng.normal(0, 7.5, days)
    sales = trend + weekly + yearly + holidays + noise
    return pd.DataFrame({"day": index, "sales": sales, "weekday": index % 7})


def load_data(seed=42, quick=False):
    frame = make_sales(210 if quick else 420, seed)
    split = int(len(frame) * 0.85)
    return {"train": frame.iloc[:split].copy(), "test": frame.iloc[split:].copy(), "full": frame}
