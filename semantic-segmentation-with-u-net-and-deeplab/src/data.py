"""Synthetic 32x32 images and masks."""
import numpy as np


def make_sample(seed=0, size=32):
    rng = np.random.default_rng(seed)
    image = np.clip(rng.normal(0.25, 0.08, (size, size)), 0, 1)
    mask = np.zeros((size, size), dtype=float)
    yy, xx = np.mgrid[0:size, 0:size]
    for _ in range(int(rng.integers(1, 3))):
        cx, cy = rng.integers(8, size - 8, 2)
        radius = rng.integers(3, 8)
        if rng.random() < 0.5:
            shape = (xx - cx) ** 2 + (yy - cy) ** 2 <= radius ** 2
        else:
            shape = np.zeros((size, size), dtype=bool)
            shape[cy - radius:cy + radius, cx - radius:cx + radius] = True
        image[shape] = rng.normal(0.82, 0.06, shape.sum())
        mask[shape] = 1.0
    return np.clip(image, 0, 1), mask


def load_data(seed=42, quick=False):
    count = 40 if quick else 180
    images, masks = [], []
    for index in range(count):
        image, mask = make_sample(seed + index, 24 if quick else 32)
        images.append(image)
        masks.append(mask)
    split = int(count * 0.8)
    return {
        "X_train": np.asarray(images[:split])[..., None],
        "y_train": np.asarray(masks[:split])[..., None],
        "X_test": np.asarray(images[split:])[..., None],
        "y_test": np.asarray(masks[split:])[..., None],
        "size": 24 if quick else 32,
    }
