"""Procedural road scenes with lane masks and vehicle boxes."""
import numpy as np


def make_scene(seed=0, size=96):
    rng = np.random.default_rng(seed)
    image = np.full((size, size), 82.0)
    image += rng.normal(0, 6, (size, size))

    yy, xx = np.mgrid[0:size, 0:size]
    horizon = int(size * 0.35)
    center = size // 2
    half_width_top = int(size * 0.12)
    half_width_bottom = int(size * 0.38)

    lane_mask = np.zeros((size, size), dtype=bool)
    for y in range(horizon, size):
        fraction = (y - horizon) / max(1, size - horizon)
        half = half_width_top + (half_width_bottom - half_width_top) * fraction
        left = int(center - half)
        right = int(center + half)
        image[y, max(0, left):min(size, right)] = 138

        edge = max(2, int(size * 0.012))
        for x in (left, right):
            x0 = max(0, x - edge)
            x1 = min(size, x + edge)
            image[y, x0:x1] = 225
            lane_mask[y, x0:x1] = True

    boxes = []
    for _ in range(int(rng.integers(1, 3))):
        width = int(rng.integers(size // 10, size // 6))
        height = int(rng.integers(size // 10, size // 6))
        x = int(rng.integers(size // 8, size - width - size // 8))
        y = int(rng.integers(horizon + 8, size - height - 4))
        image[y:y + height, x:x + width] = float(rng.integers(190, 240))
        boxes.append([x, y, x + width, y + height])

    image = np.clip(image, 0, 255)
    return {"image": image, "lane_mask": lane_mask, "boxes": boxes}


def load_data(seed=42, quick=False):
    count = 4 if quick else 14
    scenes = [make_scene(seed + offset, 64 if quick else 96) for offset in range(count)]
    return {"scenes": scenes}
