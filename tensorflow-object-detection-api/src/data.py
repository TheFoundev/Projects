"""Scenes with labelled circle/square boxes and crops."""
import numpy as np


def make_scene(seed=0, size=64):
    rng = np.random.default_rng(seed)
    image = np.clip(rng.normal(30, 6, (size, size)), 0, 255)
    boxes = []
    for _ in range(int(rng.integers(1, 4))):
        width = int(rng.integers(10, 17))
        height = int(rng.integers(10, 17))
        x = int(rng.integers(4, size - width - 4))
        y = int(rng.integers(4, size - height - 4))
        label = int(rng.integers(0, 2))
        value = float(rng.integers(180, 240))
        if label == 0:
            yy, xx = np.mgrid[0:size, 0:size]
            mask = ((xx - (x + width / 2)) ** 2 + (yy - (y + height / 2)) ** 2) <= (min(width, height) / 2) ** 2
        else:
            mask = np.zeros((size, size), dtype=bool)
            mask[y:y + height, x:x + width] = True
        image[mask] = value + rng.normal(0, 5, mask.sum())
        boxes.append([x, y, x + width, y + height, label])
    return {"image": np.clip(image, 0, 255), "boxes": boxes}


def crops(scene, size=16):
    rows = []
    labels = []
    for x0, y0, x1, y1, label in scene["boxes"]:
        crop = scene["image"][y0:y1, x0:x1]
        if crop.size == 0:
            continue
        resized = np.asarray([
            np.interp(np.linspace(0, crop.shape[1] - 1, size), np.arange(crop.shape[1]), row)
            for row in crop
        ])
        resized = np.asarray([
            np.interp(np.linspace(0, resized.shape[0] - 1, size), np.arange(resized.shape[0]), column)
            for column in resized.T
        ]).T
        rows.append(resized.reshape(-1) / 255.0)
        labels.append(label)
    return rows, labels


def load_data(seed=42, quick=False):
    count = 8 if quick else 24
    scenes = [make_scene(seed + index, 48 if quick else 64) for index in range(count)]
    X, y = [], []
    for scene in scenes:
        rows, labels = crops(scene)
        X.extend(rows)
        y.extend(labels)
    split = int(len(X) * 0.7)
    return {
        "scenes": scenes,
        "X_train": np.asarray(X[:split]),
        "y_train": np.asarray(y[:split]),
        "X_test": np.asarray(X[split:]),
        "y_test": np.asarray(y[split:]),
    }
