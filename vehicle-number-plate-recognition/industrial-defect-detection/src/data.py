"""Synthetic textured patches, some with a bright or dark defect."""
import numpy as np


def make_patch(seed=0, size=40, defective=False):
    rng = np.random.default_rng(seed)
    base = 118 + rng.normal(0, 10, (size, size))
    grain = np.sin(np.arange(size) / 2.1)[None, :] * 7 + np.sin(np.arange(size) / 3.4)[:, None] * 5
    patch = base + grain
    mask = np.zeros((size, size), dtype=bool)

    if defective:
        if rng.random() < 0.5:
            x0, y0 = rng.integers(4, size - 12, 2)
            length = rng.integers(10, 22)
            width = rng.integers(1, 3)
            for offset in range(length):
                x = x0 + offset
                if x < size:
                    patch[y0:y0 + width, x] = 220
                    mask[y0:y0 + width, x] = True
        else:
            cx, cy = rng.integers(10, size - 10, 2)
            yy, xx = np.mgrid[0:size, 0:size]
            blob = (xx - cx) ** 2 + (yy - cy) ** 2 <= rng.integers(4, 7) ** 2
            patch[blob] = 35
            mask |= blob

    return np.clip(patch, 0, 255), mask, bool(defective)


def load_data(seed=42, quick=False):
    count = 18 if quick else 60
    items = []
    for index in range(count):
        is_defect = index % 3 != 0
        patch, mask, defective_flag = make_patch(seed + index, 32 if quick else 40, is_defect)
        items.append((patch, mask, int(defective_flag)))

    split = int(count * 0.65)
    train_items = items[:split]
    test_items = items[split:]
    clean_train = [patch for patch, _, label in train_items if label == 0]
    if not clean_train:
        clean_train = [make_patch(seed + 1000 + offset, 32, False)[0] for offset in range(3)]

    return {
        "clean_train": np.asarray(clean_train),
        "X_test": np.asarray([patch for patch, _, _ in test_items]),
        "y_test": np.asarray([label for _, _, label in test_items]),
        "samples": [patch for patch, _, _ in items[:6]],
        "masks": [mask for _, mask, _ in items[:6]],
    }
