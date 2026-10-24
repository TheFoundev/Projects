"""Synthetic leaf images with four species."""
import numpy as np

SPECIES = ["clover", "lance", "broad", "serrated"]

def make_leaf(label, seed=0, size=40):
    rng = np.random.default_rng(seed)
    image = np.clip(rng.normal(30, 6, (size, size)), 0, 255)
    yy, xx = np.mgrid[0:size, 0:size]
    cx, cy = size / 2, size / 2
    width = 5 + label * 2
    height = 14 + (label % 2) * 4
    base = ((xx - cx) / width) ** 2 + ((yy - cy) / height) ** 2 <= 1

    if label == 0:
        shape = base | (np.abs(xx - cx) < 1.2) & (np.abs(yy - cy) < height)
    elif label == 1:
        shape = ((np.abs(xx - cx) / width) + (np.abs(yy - cy) / height)) <= 1
    elif label == 2:
        shape = base
    else:
        teeth = (np.sin(xx * 1.6) > 0) & (np.abs(xx - cx) < width + 2)
        shape = base & teeth

    colour = [60 + label * 25, 130 + label * 12, 55 + label * 10]
    image[shape] = np.clip(np.array(colour) + rng.normal(0, 12, 3), 0, 255).mean()
    vein = shape & (np.abs(xx - cx) < 0.8)
    image[vein] = 85
    return np.clip(image, 0, 255)

def features(image):
    yy, xx = np.where(image > 70)
    if len(xx) == 0:
        return [0.0] * 7
    width = float(xx.max() - xx.min() + 1)
    height = float(yy.max() - yy.min() + 1)
    area = float(len(xx))
    return [
        area / image.size,
        width / image.shape[1],
        height / image.shape[0],
        width / max(1.0, height),
        float(image[yy, xx].mean()) / 255.0,
        float(np.std(image[yy, xx])) / 255.0,
        float(np.mean(np.abs(np.diff(image[yy, xx])))) / 255.0,
    ]

def load_data(seed=42, quick=False):
    per_species = 12 if quick else 40
    X, y, images = [], [], []
    for label in range(len(SPECIES)):
        for sample in range(per_species):
            image = make_leaf(label, seed + label * 1000 + sample, 32 if quick else 40)
            X.append(features(image))
            y.append(label)
            images.append(image)
    X = np.asarray(X)
    y = np.asarray(y)
    split = int(len(X) * 0.75)
    return {
        "X_train": X[:split], "y_train": y[:split],
        "X_test": X[split:], "y_test": y[split:],
        "species": SPECIES, "images": images[:8],
    }
