"""Three kinds of short series: sine, square and trend."""
import numpy as np

CLASSES = ["sine", "square", "trend"]


def make_series(label, seed=0, length=64):
    rng = np.random.default_rng(seed)
    time = np.arange(length) / length
    if label == 0:
        values = np.sin(2 * np.pi * rng.uniform(1.5, 3.5) * time)
    elif label == 1:
        frequency = rng.uniform(1.5, 3.5)
        values = np.sign(np.sin(2 * np.pi * frequency * time))
    else:
        values = np.linspace(-1, 1, length) + 0.3 * np.sin(2 * np.pi * 2 * time)
    values = values + rng.normal(0, 0.08, length)
    return values.astype("float32")


def load_data(seed=42, quick=False):
    per_class = 30 if quick else 100
    X, y = [], []
    for label in range(3):
        for sample in range(per_class):
            X.append(make_series(label, seed + label * 1000 + sample))
            y.append(label)
    X = np.asarray(X)
    y = np.asarray(y)
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(X))
    X, y = X[order], y[order]
    split = int(len(X) * 0.75)
    return {"X_train": X[:split], "y_train": y[:split], "X_test": X[split:], "y_test": y[split:], "classes": CLASSES}
