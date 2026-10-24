"""Draw simple synthetic faces with two binary attributes."""
import numpy as np


def draw_face(seed=0, size=32):
    rng = np.random.default_rng(seed)
    image = rng.normal(0.86, 0.03, (size, size))
    has_glasses = bool(rng.random() < 0.5)
    smiling = bool(rng.random() < 0.5)

    yy, xx = np.mgrid[0:size, 0:size]
    face = ((xx - size / 2) ** 2 / (size * 0.32) ** 2 + (yy - size / 2) ** 2 / (size * 0.40) ** 2) <= 1
    image[face] = 0.72 + rng.normal(0, 0.02, face.sum())

    for eye_x in (int(size * 0.36), int(size * 0.64)):
        eye = (xx - eye_x) ** 2 + (yy - int(size * 0.44)) ** 2 <= 2.2 ** 2
        image[eye] = 0.18

    if has_glasses:
        for eye_x in (int(size * 0.36), int(size * 0.64)):
            ring = np.abs(np.sqrt((xx - eye_x) ** 2 + (yy - int(size * 0.44)) ** 2) - 5) < 1.1
            image[ring] = 0.1
        bridge = (np.abs(yy - int(size * 0.44)) < 1) & (xx > int(size * 0.36)) & (xx < int(size * 0.64))
        image[bridge] = 0.1

    mouth_y = int(size * 0.68)
    if smiling:
        curve = (np.abs((xx - size / 2)) < size * 0.18) & (np.abs(yy - mouth_y - (xx - size / 2) ** 2 * 0.02) < 1.2)
    else:
        curve = (np.abs(xx - size / 2) < size * 0.16) & (np.abs(yy - mouth_y) < 1.0)
    image[curve] = 0.15

    return np.clip(image, 0, 1), has_glasses, smiling


def load_data(seed=42, quick=False):
    count = 60 if quick else 220
    images, glasses, smiles = [], [], []
    for index in range(count):
        image, has_glasses, smiling = draw_face(seed + index)
        images.append(image)
        glasses.append(int(has_glasses))
        smiles.append(int(smiling))

    X = np.asarray(images).reshape(count, -1)
    split = int(count * 0.75)
    return {
        "X_train": X[:split],
        "X_test": X[split:],
        "y_glasses_train": np.asarray(glasses[:split]),
        "y_glasses_test": np.asarray(glasses[split:]),
        "y_smile_train": np.asarray(smiles[:split]),
        "y_smile_test": np.asarray(smiles[split:]),
        "sample_image": images[-1],
        "sample_true": {"glasses": bool(glasses[-1]), "smiling": bool(smiles[-1])},
    }
