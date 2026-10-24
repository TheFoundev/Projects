"""Proposals from components, class from crop features."""
import numpy as np
from scipy import ndimage
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score


def proposal_boxes(image, threshold=150, min_area=30):
    labels, count = ndimage.label(image > threshold)
    boxes = []
    for label in range(1, count + 1):
        ys, xs = np.where(labels == label)
        if len(xs) < min_area:
            continue
        boxes.append([int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1])
    return boxes


def box_iou(first, second):
    x0, y0 = max(first[0], second[0]), max(first[1], second[1])
    x1, y1 = min(first[2], second[2]), min(first[3], second[3])
    intersection = max(0, x1 - x0) * max(0, y1 - y0)
    area_a = (first[2] - first[0]) * (first[3] - first[1])
    area_b = (second[2] - second[0]) * (second[3] - second[1])
    return intersection / max(1, area_a + area_b - intersection)


def train(data, quick=False):
    model = RandomForestClassifier(n_estimators=50 if quick else 160, max_depth=8, random_state=6)
    model.fit(data["X_train"], data["y_train"])
    class_accuracy = accuracy_score(data["y_test"], model.predict(data["X_test"]))

    true_positive = false_positive = false_negative = 0
    for scene in data["scenes"]:
        proposals = proposal_boxes(scene["image"])
        matched = set()
        for truth in scene["boxes"]:
            best = 0.0
            best_index = -1
            for index, proposal in enumerate(proposals):
                if index in matched:
                    continue
                overlap = box_iou(truth, proposal)
                if overlap > best:
                    best = overlap
                    best_index = index
            if best >= 0.4:
                true_positive += 1
                matched.add(best_index)
            else:
                false_negative += 1
        false_positive += len(proposals) - len(matched)

    precision = true_positive / max(1, true_positive + false_positive)
    recall = true_positive / max(1, true_positive + false_negative)
    return model, {
        "class_accuracy": round(float(class_accuracy), 4),
        "box_precision": round(float(precision), 4),
        "box_recall": round(float(recall), 4),
        "crops": int(len(data["X_train"]) + len(data["X_test"])),
    }


def demo(data):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from pathlib import Path

    model, metrics = train(data, quick=True)
    scene = data["scenes"][0]
    proposals = proposal_boxes(scene["image"])
    print(f"Proposals: {len(proposals)}, ground truth: {len(scene['boxes'])}")
    print(f"Class accuracy: {metrics['class_accuracy']:.2f}, box recall: {metrics['box_recall']:.2f}")

    Path("artifacts").mkdir(exist_ok=True)
    fig, axis = plt.subplots(figsize=(4.5, 4.5))
    axis.imshow(scene["image"], cmap="gray")
    for x0, y0, x1, y1 in proposals:
        axis.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, edgecolor="#22c55e"))
    axis.axis("off")
    fig.tight_layout()
    fig.savefig("artifacts/object_detection.png", dpi=120)
    plt.close(fig)
