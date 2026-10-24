"""Synthetic shape images and their ground-truth masks."""
import numpy as np


def make_sample(seed=0, size=64):
    rng = np.random.default_rng(seed)
    image = np.clip(rng.normal(35, 8, (size, size)), 0, 255)
    masks = []

    count = int(rng.integers(1, 4))
    # Every object gets its own part of the picture, so two of them are never
    # one blob and the ground truth is unambiguous.
    spots = [
        (size // 4, size // 4),
        (size * 3 // 4, size // 4),
        (size // 2, size * 3 // 4),
    ]
    for index in range(count):
        mask = np.zeros((size, size), dtype=bool)
        cx = int(spots[index][0] + rng.integers(-4, 5))
        cy = int(spots[index][1] + rng.integers(-4, 5))
        radius = int(rng.integers(6, 11))
        if rng.random() < 0.5:
            yy, xx = np.mgrid[0:size, 0:size]
            mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= radius ** 2
        else:
            x0, x1 = max(0, cx - radius), min(size, cx + radius)
            y0, y1 = max(0, cy - radius), min(size, cy + radius)
            mask[y0:y1, x0:x1] = True
        value = float(rng.integers(170, 245))
        image[mask] = value + rng.normal(0, 6, mask.sum())
        masks.append(mask)

    return {"image": np.clip(image, 0, 255), "masks": masks}


def load_data(seed=42, quick=False):
    count = 4 if quick else 12
    return {"samples": [make_sample(seed + i, 48 if quick else 64) for i in range(count)]}
