"""Three synthetic 2D distributions with labelled outliers."""
import numpy as np


def gaussian(seed=0):
    rng = np.random.default_rng(seed)
    normal = rng.normal(0, 1, (160, 2))
    outliers = rng.normal(0, 4.5, (18, 2))
    return np.vstack([normal, outliers]), np.array([0] * 160 + [1] * 18)


def ring(seed=1):
    rng = np.random.default_rng(seed)
    angles = rng.uniform(0, 2 * np.pi, 150)
    radius = rng.normal(2.4, 0.18, 150)
    normal = np.column_stack([radius * np.cos(angles), radius * np.sin(angles)])
    outliers = rng.uniform(-4, 4, (18, 2))
    return np.vstack([normal, outliers]), np.array([0] * 150 + [1] * 18)


def clustered(seed=2):
    rng = np.random.default_rng(seed)
    groups = []
    for center in [(-2, -1), (2, 1), (0, 3)]:
        groups.append(rng.normal(center, 0.45, (55, 2)))
    normal = np.vstack(groups)
    outliers = rng.uniform(-6, 6, (18, 2))
    return np.vstack([normal, outliers]), np.array([0] * len(normal) + [1] * 18)


def load_data(seed=42, quick=False):
    datasets = {"gaussian": gaussian(seed), "ring": ring(seed + 1), "clustered": clustered(seed + 2)}
    return {"datasets": datasets}
