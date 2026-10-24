"""Simulated daily series with trend, weekly pattern and noise."""
import numpy as np
import pandas as pd


def make_series(days=240, seed=42):
    rng = np.random.default_rng(seed)
    index = np.arange(days)
    trend = 40 + index * 0.09
    weekly = 6 * np.sin(2 * np.pi * index / 7)
    monthly = 3 * np.sin(2 * np.pi * index / 30)
    noise = rng.normal(0, 2.2, days)
    values = trend + weekly + monthly + noise
    return pd.DataFrame({"day": index, "value": values})


def load_data(seed=42, quick=False):
    frame = make_series(120 if quick else 240, seed)
    split = int(len(frame) * 0.8)
    return {"train": frame.iloc[:split].copy(), "test": frame.iloc[split:].copy(), "full": frame}
