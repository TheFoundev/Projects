"""Synthetic 3D volumes with a bright spherical lesion."""
import numpy as np


def make_volume(seed=0, size=24):
    rng = np.random.default_rng(seed)
    volume = rng.normal(0.30, 0.05, (size, size, size))
    mask = np.zeros((size, size, size), dtype=bool)
    label = 0

    if rng.random() < 0.55:
        cx, cy, cz = rng.integers(6, size - 6, 3)
        radius = rng.integers(2, 5)
        zz, yy, xx = np.mgrid[0:size, 0:size, 0:size]
        mask = (xx - cx) ** 2 + (yy - cy) ** 2 + (zz - cz) ** 2 <= radius ** 2
        volume[mask] = rng.normal(0.78, 0.06, mask.sum())
        label = 1

    volume = np.clip(volume, 0, 1)
    return volume.astype("float32"), mask, label


def load_data(seed=42, quick=False):
    count = 10 if quick else 30
    volumes, masks, labels = [], [], []
    for index in range(count):
        volume, mask, label = make_volume(seed + index, 20 if quick else 24)
        volumes.append(volume)
        masks.append(mask)
        labels.append(label)

    split = int(count * 0.7)
    return {
        "train": list(zip(volumes[:split], masks[:split], labels[:split])),
        "test": list(zip(volumes[split:], masks[split:], labels[split:])),
        "sample": (volumes[-1], masks[-1], labels[-1]),
    }
