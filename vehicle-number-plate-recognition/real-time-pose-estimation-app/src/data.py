"""Generate a short sequence of a moving stick figure."""
import numpy as np

JOINTS = ["head", "neck", "left_hand", "right_hand", "hip", "left_foot", "right_foot"]


def make_frame(frame=0, size=64):
    rng = np.random.default_rng(100 + frame)
    image = np.clip(rng.normal(22, 4, (size, size)), 0, 255)
    center_x = int(size / 2 + 12 * np.sin(frame / 2.5))
    top = 8
    height = int(size * 0.72)
    neck_y = top + int(height * 0.18)
    hip_y = top + int(height * 0.58)
    head = (center_x, top + 4)
    yy, xx = np.mgrid[0:size, 0:size]
    image[(xx - head[0]) ** 2 + (yy - head[1]) ** 2 <= 4 ** 2] = 240

    limbs = [
        ((center_x, neck_y), (center_x, hip_y)),
        ((center_x, neck_y), (center_x - int(12 + 4 * np.sin(frame / 2)), neck_y + 16)),
        ((center_x, neck_y), (center_x + int(12 + 4 * np.cos(frame / 2)), neck_y + 16)),
        ((center_x, hip_y), (center_x - 9, top + height)),
        ((center_x, hip_y), (center_x + 9, top + height)),
    ]
    for (x0, y0), (x1, y1) in limbs:
        steps = max(abs(x1 - x0), abs(y1 - y0)) + 1
        for step in range(steps):
            fraction = step / max(1, steps - 1)
            x = int(x0 + (x1 - x0) * fraction)
            y = int(y0 + (y1 - y0) * fraction)
            image[max(0, y - 1):min(size, y + 2), max(0, x - 1):min(size, x + 2)] = 225

    joints = np.array([
        head, (center_x, neck_y), (center_x - 12, neck_y + 16), (center_x + 12, neck_y + 16),
        (center_x, hip_y), (center_x - 9, top + height), (center_x + 9, top + height),
    ], dtype=float)
    return {"image": np.clip(image, 0, 255), "joints": joints, "frame": frame}


def load_data(seed=42, quick=False):
    count = 5 if quick else 16
    return {"frames": [make_frame(index) for index in range(count)]}
