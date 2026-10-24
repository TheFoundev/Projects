"""Synthetic daily prices with a slow trend and a short cycle."""
import numpy as np
import pandas as pd


def make_prices(days=420, seed=42):
    rng = np.random.default_rng(seed)
    index = np.arange(days)
    drift = 0.0005
    cycle = 0.0011 * np.sin(index / 17.0)
    returns = drift + cycle + rng.normal(0, 0.012, days)
    close = 100 * np.exp(np.cumsum(returns))
    open_price = close * (1 + rng.normal(0, 0.002, days))
    high = np.maximum(open_price, close) * (1 + np.abs(rng.normal(0, 0.004, days)))
    low = np.minimum(open_price, close) * (1 - np.abs(rng.normal(0, 0.004, days)))
    volume = rng.integers(800_000, 3_000_000, days)
    return pd.DataFrame({
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    })


def load_data(seed=42, quick=False):
    prices = make_prices(180 if quick else 420, seed)
    split = int(len(prices) * 0.75)
    return {"prices": prices, "train": prices.iloc[:split].copy(), "test": prices.iloc[split:].copy()}
