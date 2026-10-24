"""Generate tiny shape images for the GAN."""
import numpy as np


def make_images(count=128, size=16, seed=0):
    rng = np.random.default_rng(seed)
    images = np.zeros((count, size, size), dtype=float)
    yy, xx = np.mgrid[0:size, 0:size]

    for index in range(count):
        if rng.random() < 0.5:
            cx, cy = rng.integers(4, size - 4, 2)
            radius = rng.integers(2, 5)
            mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= radius ** 2
        else:
            x0, y0 = rng.integers(2, size - 7, 2)
            width, height = rng.integers(3, 7, 2)
            mask = np.zeros((size, size), dtype=bool)
            mask[y0:y0 + height, x0:x0 + width] = True
        images[index][mask] = 1.0

    images = (images * 2 - 1).astype("float32")
    return images.reshape(count, size, size, 1)


def load_data(seed=42, quick=False):
    return {"images": make_images(48 if quick else 160, seed=seed), "size": 16}
