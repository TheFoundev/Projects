"""Synthetic wake phrase and negative clips."""
import numpy as np

SAMPLE_RATE = 8000

def wake_clip(seed=0):
    rng = np.random.default_rng(seed)
    parts = []
    for frequency in (480, 640, 760, 920):
        time = np.arange(int(SAMPLE_RATE * 0.11)) / SAMPLE_RATE
        envelope = np.sin(np.linspace(0, np.pi, len(time))) ** 0.5
        parts.append(0.5 * np.sin(2 * np.pi * frequency * time) * envelope)
        parts.append(np.zeros(int(SAMPLE_RATE * 0.025)))
    signal = np.concatenate(parts)
    signal += rng.normal(0, 0.02, len(signal))
    return signal / (np.max(np.abs(signal)) + 1e-9)

def negative_clip(seed=0):
    rng = np.random.default_rng(seed)
    duration = 0.55
    time = np.arange(int(SAMPLE_RATE * duration)) / SAMPLE_RATE
    mode = seed % 3
    if mode == 0:
        signal = rng.normal(0, 0.12, len(time))
    elif mode == 1:
        signal = 0.25 * np.sin(2 * np.pi * rng.uniform(200, 400) * time)
        signal += rng.normal(0, 0.05, len(time))
    else:
        signal = 0.2 * np.sign(np.sin(2 * np.pi * rng.uniform(3, 8) * time))
        signal += rng.normal(0, 0.04, len(time))
    return signal / (np.max(np.abs(signal)) + 1e-9)

def features(signal, frames=20, bands=10):
    length = max(16, len(signal) // frames)
    window = np.hanning(length)
    rows = []
    for index in range(frames):
        chunk = signal[index * length:(index + 1) * length]
        if len(chunk) < length:
            chunk = np.pad(chunk, (0, length - len(chunk)))
        spectrum = np.abs(np.fft.rfft(chunk * window)) ** 2
        edges = np.linspace(1, len(spectrum), bands + 1).astype(int)
        rows.append(np.log1p([spectrum[edges[i]:max(edges[i] + 1, edges[i + 1])].mean() for i in range(bands)]))
    return np.asarray(rows).reshape(-1)

def load_data(seed=42, quick=False):
    count = 30 if quick else 120
    X, y = [], []
    for index in range(count):
        positive = index % 2 == 0
        signal = wake_clip(seed + index) if positive else negative_clip(seed + index)
        X.append(features(signal))
        y.append(int(positive))
    X = np.asarray(X)
    y = np.asarray(y)
    split = int(len(X) * 0.75)
    return {"X_train": X[:split], "y_train": y[:split], "X_test": X[split:], "y_test": y[split:]}
