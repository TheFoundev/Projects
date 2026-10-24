"""Bounding-box heuristics for two-person joint estimation."""
import numpy as np

from src.data import JOINT_NAMES


def estimate(image, threshold=120):
    ys, xs = np.where(image > threshold)
    if len(xs) < 10:
        return []
    middle = (xs.min() + xs.max()) / 2
    groups = [xs < middle, xs >= middle]
    people = []

    for group in groups:
        if group.sum() < 10:
            continue
        gx, gy = xs[group], ys[group]
        x0, x1 = gx.min(), gx.max()
        y0, y1 = gy.min(), gy.max()
        width = max(1, x1 - x0)
        height = max(1, y1 - y0)
        center = (x0 + x1) / 2
        people.append(np.array([
            [center, y0 + height * 0.06],
            [center, y0 + height * 0.20],
            [x0 + width * 0.05, y0 + height * 0.46],
            [x1 - width * 0.05, y0 + height * 0.46],
            [center, y0 + height * 0.58],
            [center - width * 0.25, y1],
            [center + width * 0.25, y1],
        ]))
    return people


def pck(predicted, truth, tolerance_ratio=0.12, size=72):
    if len(predicted) != len(truth):
        return 0.0, len(truth)
    tolerance = tolerance_ratio * size
    correct = 0
    total = 0
    for person_prediction, person_truth in zip(predicted, truth):
        distances = np.linalg.norm(person_prediction - person_truth, axis=1)
        correct += int((distances <= tolerance).sum())
        total += len(person_truth)
    return correct / max(1, total), total


def train(data, quick=False):
    best = None
    for threshold in (100, 120, 140, 160):
        scores = []
        joints = 0
        for scene in data["scenes"]:
            predicted = estimate(scene["image"], threshold)
            value, count = pck(predicted, scene["joints"], size=scene["image"].shape[0])
            scores.append(value)
            joints += count
        result = (float(np.mean(scores)), threshold, joints)
        if best is None or result[0] > best[0]:
            best = result
    return {"threshold": best[1]}, {
        "pck": round(float(best[0]), 4),
        "threshold": best[1],
        "joints_evaluated": int(best[2]),
        "people": 2,
    }


def demo(data):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from pathlib import Path

    model, metrics = train(data, quick=True)
    scene = data["scenes"][0]
    predicted = estimate(scene["image"], model["threshold"])
    value, _ = pck(predicted, scene["joints"], size=scene["image"].shape[0])
    print(f"Detected {len(predicted)} people; PCK on this frame: {value:.2f}")
    for index, person in enumerate(predicted):
        print(f"  person {index + 1}: head at ({person[0][0]:.0f}, {person[0][1]:.0f})")

    Path("artifacts").mkdir(exist_ok=True)
    fig, axis = plt.subplots(figsize=(4.5, 4.5))
    axis.imshow(scene["image"], cmap="gray")
    colors = ["#ef4444", "#3b82f6"]
    for person_index, person in enumerate(predicted):
        axis.scatter(person[:, 0], person[:, 1], s=16, c=colors[person_index % 2])
    axis.set_title("estimated joints")
    axis.axis("off")
    fig.tight_layout()
    fig.savefig("artifacts/pose_estimate.png", dpi=120)
    plt.close(fig)
