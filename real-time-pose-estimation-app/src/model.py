"""A top-down pose estimator: a detector, a trained keypoint regressor and the metrics."""
import json
import os
from pathlib import Path

import numpy as np

#: The joints the estimator answers with, in the order they are stored.
JOINT_NAMES = ["head", "neck", "left_hand", "right_hand", "hip", "left_foot", "right_foot"]

#: The size of the grid the crop is reduced to before the regression.
GRID = 8

#: The fraction of the size of the box that counts as a hit.
PCK_ALPHA = 0.2


# ---------------------------------------------------------------------------
# The detector
# ---------------------------------------------------------------------------


def find_people(image, threshold=120, min_pixels=12, max_aspect=4.0, tolerance=0.18):
    """The boxes of the people in the image.

    The bright pixels are grouped into blobs, and a blob that is tall
    enough and not too wide is a person.
    """
    bright = np.asarray(image, dtype=float) > threshold
    if not bright.any():
        return []

    # A depth first labelling of the bright pixels, without scipy.
    height, width = bright.shape
    labels = np.zeros((height, width), dtype=int)
    current = 0
    blobs = []
    neighbours = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))

    for y in range(height):
        for x in range(width):
            if not bright[y, x] or labels[y, x]:
                continue
            current += 1
            stack = [(y, x)]
            labels[y, x] = current
            pixels = []
            while stack:
                cy, cx = stack.pop()
                pixels.append((cy, cx))
                for dy, dx in neighbours:
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < height and 0 <= nx < width and bright[ny, nx] and not labels[ny, nx]:
                        labels[ny, nx] = current
                        stack.append((ny, nx))
            blobs.append(pixels)

    boxes = []
    for pixels in blobs:
        if len(pixels) < min_pixels:
            continue
        ys = [p[0] for p in pixels]
        xs = [p[1] for p in pixels]
        y0, y1 = min(ys), max(ys)
        x0, x1 = min(xs), max(xs)
        width_box = max(1, x1 - x0)
        height_box = max(1, y1 - y0)
        if height_box / width_box > max_aspect:
            continue
        boxes.append({
            "x0": float(x0), "y0": float(y0), "x1": float(x1), "y1": float(y1),
            "pixels": len(pixels),
        })

    return merge_parts(boxes, tolerance * width)


def merge_parts(boxes, tolerance=8.0):
    """Join the parts of a person into one box.

    A person is drawn in pieces: the head, the arms and the legs are often
    separate blobs. The parts of one person stand in a column, so the blobs
    whose middle is close together belong to the same person.
    """
    if not boxes:
        return []

    limit = max(2.0, tolerance)
    groups: list[list[dict]] = []
    for box in sorted(boxes, key=lambda item: (item["x0"] + item["x1"]) / 2):
        middle = (box["x0"] + box["x1"]) / 2
        for group in groups:
            group_middle = sum((item["x0"] + item["x1"]) / 2 for item in group) / len(group)
            if abs(middle - group_middle) <= limit:
                group.append(box)
                break
        else:
            groups.append([box])

    merged = []
    for group in groups:
        merged.append({
            "x0": min(item["x0"] for item in group),
            "y0": min(item["y0"] for item in group),
            "x1": max(item["x1"] for item in group),
            "y1": max(item["y1"] for item in group),
            "pixels": sum(item["pixels"] for item in group),
            "parts": len(group),
        })
    return merged


# ---------------------------------------------------------------------------
# The features
# ---------------------------------------------------------------------------


def crop_features(image, box, grid=GRID):
    """The features of the person in the box.

    The crop is reduced to a small grid of mean brightness, which says
    where the limbs are, and the size of the box is added.
    """
    values = np.asarray(image, dtype=float)
    y0 = max(0, int(box["y0"]))
    y1 = min(values.shape[0], int(box["y1"]) + 1)
    x0 = max(0, int(box["x0"]))
    x1 = min(values.shape[1], int(box["x1"]) + 1)
    crop = values[y0:y1, x0:x1]
    if crop.size == 0:
        return np.zeros(grid * grid + 2, dtype=float)

    rows = np.array_split(np.arange(crop.shape[0]), min(grid, crop.shape[0]))
    columns = np.array_split(np.arange(crop.shape[1]), min(grid, crop.shape[1]))

    cells = []
    for row in rows:
        for column in columns:
            if len(row) == 0 or len(column) == 0:
                cells.append(0.0)
            else:
                cells.append(float(crop[np.ix_(row, column)].mean()))

    width = max(1.0, box["x1"] - box["x0"])
    height = max(1.0, box["y1"] - box["y0"])
    return np.array(cells + [width, height], dtype=float)


def target_joints(joints, box):
    """The joints of a person, relative to the box they are in."""
    width = max(1.0, box["x1"] - box["x0"])
    height = max(1.0, box["y1"] - box["y0"])
    return np.array(
        [[(point[0] - box["x0"]) / width, (point[1] - box["y0"]) / height] for point in joints],
        dtype=float,
    )


# ---------------------------------------------------------------------------
# The regressor
# ---------------------------------------------------------------------------


def fit_ridge(features, targets, alpha=1.0):
    """Fit the regressor with a ridge regression.

    The solution is the closed form of the normal equations, so there is no
    iteration and no random seed to worry about.
    """
    features = np.asarray(features, dtype=float)
    targets = np.asarray(targets, dtype=float)
    # The joints are flattened, so the regression is one matrix product.
    flat = targets.reshape(len(targets), -1)
    gram = features.T @ features + alpha * np.eye(features.shape[1])
    weights = np.linalg.solve(gram, features.T @ flat)
    return {"weights": weights, "alpha": alpha, "grid": GRID, "joints": len(targets[0])}


def predict_joints(features, weights, box):
    """The joints of a person, in the image."""
    prediction = np.asarray(features, dtype=float) @ np.asarray(weights["weights"], dtype=float)
    prediction = prediction.reshape(-1, 2)
    width = max(1.0, box["x1"] - box["x0"])
    height = max(1.0, box["y1"] - box["y0"])
    return np.array(
        [[box["x0"] + value[0] * width, box["y0"] + value[1] * height] for value in prediction],
        dtype=float,
    )


# ---------------------------------------------------------------------------
# The metrics
# ---------------------------------------------------------------------------


def pck(predicted, truth, alpha=PCK_ALPHA):
    """The share of the joints that are close enough.

    A joint counts as a hit when it is within a fraction of the size of the
    body, which is how the PCK is defined.
    """
    if predicted is None or truth is None or len(truth) == 0:
        return 0.0
    scale = float(np.linalg.norm(truth.max(axis=0) - truth.min(axis=0)))
    limit = max(1e-6, alpha * scale)
    distances = np.linalg.norm(np.asarray(predicted) - np.asarray(truth), axis=1)
    return float((distances <= limit).mean())


def mean_joint_error(predicted, truth):
    """The average distance between the predicted and the true joints."""
    if predicted is None or truth is None or len(truth) == 0:
        return float("inf")
    return float(np.linalg.norm(np.asarray(predicted) - np.asarray(truth), axis=1).mean())


# ---------------------------------------------------------------------------
# The model
# ---------------------------------------------------------------------------


def build_training_set(frames):
    """The features and the targets of the training frames."""
    features = []
    targets = []
    for frame in frames:
        boxes = find_people(frame["image"])
        if not boxes:
            continue
        box = boxes[0]
        features.append(crop_features(frame["image"], box))
        targets.append(target_joints(frame["joints"], box))
    if not features:
        return np.zeros((0, GRID * GRID + 2)), np.zeros((0, len(JOINT_NAMES), 2))
    return np.array(features), np.array(targets)


def train(data, quick=False):
    """Fit the keypoint regressor on the frames."""
    frames = data["frames"]
    features, targets = build_training_set(frames)
    if len(features) == 0:
        raise ValueError("there is no person in the training frames")

    weights = fit_ridge(features, targets)

    errors = []
    hits = []
    for frame in frames:
        boxes = find_people(frame["image"])
        if not boxes:
            continue
        box = boxes[0]
        predicted = predict_joints(crop_features(frame["image"], box), weights, box)
        errors.append(mean_joint_error(predicted, frame["joints"]))
        hits.append(pck(predicted, frame["joints"]))

    return weights, {
        "mean_joint_error": round(float(np.mean(errors)), 3),
        "pck": round(float(np.mean(hits)), 4),
        "frames": len(frames),
        "joints_per_frame": len(JOINT_NAMES),
    }


def estimate(image, weights, threshold=120):
    """The pose of every person in the image."""
    people = []
    for box in find_people(image, threshold):
        joints = predict_joints(crop_features(image, box), weights, box)
        people.append({"box": box, "joints": joints})
    return people


def save_model(weights, path="artifacts/model.json"):
    """Save the weights of the model."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "weights": np.asarray(weights["weights"]).tolist(),
        "joints": weights.get("joints", len(JOINT_NAMES)),
        "alpha": weights["alpha"],
        "grid": weights["grid"],
        "joint_names": JOINT_NAMES,
    }
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(target)


def load_model(path="artifacts/model.json"):
    """Read the weights of the model back."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return {
        "weights": np.array(payload["weights"]),
        "alpha": payload.get("alpha", 1.0),
        "grid": payload.get("grid", GRID),
        "joints": payload.get("joints", len(JOINT_NAMES)),
    }


def demo(data):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from pathlib import Path

    weights, metrics = train(data, quick=True)
    frame = data["frames"][-1]
    people = estimate(frame["image"], weights)

    print(f"Frame {frame['frame']}: mean joint error {metrics['mean_joint_error']:.2f}px, PCK {metrics['pck']:.2f}")
    for index, person in enumerate(people):
        print(f"  person {index}:", [(name, [round(value) for value in point]) for name, point in zip(JOINT_NAMES, person["joints"])])

    Path("artifacts").mkdir(exist_ok=True)
    fig, axis = plt.subplots(figsize=(4.5, 4.5))
    axis.imshow(frame["image"], cmap="gray")
    for person in people:
        axis.scatter(person["joints"][:, 0], person["joints"][:, 1], c="#22c55e", s=20)
    axis.scatter(frame["joints"][:, 0], frame["joints"][:, 1], c="#ef4444", s=16, marker="x")
    axis.set_title("pose estimate (green) and truth (red)")
    axis.axis("off")
    fig.tight_layout()
    fig.savefig("artifacts/pose_frame.png", dpi=120)
    plt.close(fig)
