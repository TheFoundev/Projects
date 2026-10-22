"""Synthetic images, a point prompt and the true mask."""
import numpy as np


def make_sample(seed=0, size=48):
    rng = np.random.default_rng(seed)
    image = np.clip(rng.normal(38, 8, (size, size)), 0, 255)
    masks = []
    for _ in range(int(rng.integers(1, 3))):
        mask = np.zeros((size, size), dtype=bool)
        cx, cy = rng.integers(12, size - 12, 2)
        radius = rng.integers(6, 11)
        if rng.random() < 0.5:
            yy, xx = np.mgrid[0:size, 0:size]
            mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= radius ** 2
        else:
            mask[cy - radius:cy + radius, cx - radius:cx + radius] = True
        image[mask] = rng.normal(190, 9, mask.sum())
        masks.append(mask)

    target = int(rng.integers(0, len(masks)))
    ys, xs = np.where(masks[target])
    point = (int(xs[len(xs) // 2]), int(ys[len(ys) // 2]))
    return {"image": np.clip(image, 0, 255), "mask": masks[target], "point": point}


def load_data(seed=42, quick=False):
    count = 4 if quick else 14
    return {"samples": [make_sample(seed + index, 40 if quick else 48) for index in range(count)]}
