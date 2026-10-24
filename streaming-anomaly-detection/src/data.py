"""A stream with slow drift, noise and short anomaly spikes."""
import numpy as np


def make_stream(count=600, seed=42):
    rng = np.random.default_rng(seed)
    index = np.arange(count)
    base = 50 + 0.02 * index + 3 * np.sin(index / 20)
    values = base + rng.normal(0, 1.2, count)
    labels = np.zeros(count, dtype=int)
    for center in (90, 180, 300, 410, 520):
        width = int(rng.integers(3, 7))
        amplitude = float(rng.choice([-1, 1]) * rng.uniform(8, 15))
        values[center:center + width] += amplitude
        labels[center:center + width] = 1
    return {"values": values, "labels": labels, "timestamps": index}


def load_data(seed=42, quick=False):
    return make_stream(260 if quick else 600, seed)
