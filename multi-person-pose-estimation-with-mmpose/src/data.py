"""Draw two stick figures and record their joint coordinates."""
import numpy as np

JOINT_NAMES = ["head", "neck", "left_hand", "right_hand", "hip", "left_foot", "right_foot"]


def draw_line(image, x0, y0, x1, y1, value=230):
    steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for step in range(steps):
        fraction = step / max(1, steps - 1)
        x = int(x0 + (x1 - x0) * fraction)
        y = int(y0 + (y1 - y0) * fraction)
        if 0 <= y < image.shape[0] and 0 <= x < image.shape[1]:
            image[max(0, y - 1):min(image.shape[0], y + 2), max(0, x - 1):min(image.shape[1], x + 2)] = value


def draw_person(image, center_x, top, height, seed=0):
    rng = np.random.default_rng(seed)
    head = (center_x, top + 5)
    neck = (center_x, top + 12)
    hip = (center_x, top + int(height * 0.58))
    left_hand = (center_x - int(height * 0.22), top + int(height * 0.40))
    right_hand = (center_x + int(height * 0.22), top + int(height * 0.40))
    left_foot = (center_x - int(height * 0.14), top + height)
    right_foot = (center_x + int(height * 0.14), top + height)

    yy, xx = np.mgrid[0:image.shape[0], 0:image.shape[1]]
    head_mask = (xx - head[0]) ** 2 + (yy - head[1]) ** 2 <= 4 ** 2
    image[head_mask] = 245

    for start, end in [(neck, hip), (neck, left_hand), (neck, right_hand), (hip, left_foot), (hip, right_foot)]:
        draw_line(image, start[0], start[1], end[0], end[1])

    joints = np.array([head, neck, left_hand, right_hand, hip, left_foot, right_foot], dtype=float)
    joints += rng.normal(0, 0.6, joints.shape)
    return joints


def make_scene(seed=0, size=72, people=2):
    rng = np.random.default_rng(seed)
    image = np.clip(rng.normal(24, 5, (size, size)), 0, 255)
    joints = []
    centers = [size * 0.33, size * 0.67][:people]
    for index, center in enumerate(centers):
        top = int(rng.integers(8, 14))
        height = int(rng.integers(size // 2, int(size * 0.72)))
        joints.append(draw_person(image, int(center + rng.integers(-3, 4)), top, height, seed + index))
    return {"image": np.clip(image, 0, 255), "joints": joints}


def load_data(seed=42, quick=False):
    count = 4 if quick else 14
    return {"scenes": [make_scene(seed + index, 56 if quick else 72) for index in range(count)]}
