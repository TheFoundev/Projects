"""Classical perception baseline: thresholds, labels and IoU.

The lane threshold is fitted on a part of the scenes and the metrics are
measured on the rest, so the numbers are not the ones the threshold was
chosen for.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage

#: The thresholds the lane detector is tried with.
LANE_THRESHOLDS = (170, 180, 190, 200, 210)

#: The IoU two boxes have to reach before they are the same object.
MATCH_IOU = 0.3


def lane_iou(predicted, truth):
    """The share of the lane pixels that were found."""
    intersection = np.logical_and(predicted, truth).sum()
    union = np.logical_or(predicted, truth).sum()
    return float(intersection / union) if union else 1.0


def detect_vehicles(image, threshold=175, min_area=18, max_area=900):
    """The boxes of the vehicles in a scene.

    A vehicle is a blob of bright pixels that is not too small, not too big
    and not too thin. The lane edges are bright as well, so they are told
    apart by their shape: they are long and thin, a vehicle is not.
    """
    mask = image > threshold
    # The edge of the lane is a thin strip that can touch a vehicle, so the
    # mask is thinned first: the strip disappears and the vehicle stays. The
    # boxes are one pixel larger again afterwards.
    mask = ndimage.binary_erosion(mask, structure=np.ones((3, 3)), iterations=1)
    labels, count = ndimage.label(mask)
    boxes = []
    for label in range(1, count + 1):
        ys, xs = np.where(labels == label)
        area = len(xs)
        if not (min_area <= area <= max_area):
            continue
        width = xs.max() - xs.min() + 1
        height = ys.max() - ys.min() + 1
        if width < 4 or height < 4:
            continue
        if width / height > 5 or height / width > 5:
            continue
        # A vehicle is a solid block. The edge of the lane is a thin strip that
        # crosses the picture diagonally, so it fills only a small part of its
        # own box and is not a vehicle.
        if area / float(width * height) < 0.4:
            continue
        boxes.append([
            max(0, int(xs.min()) - 1),
            max(0, int(ys.min()) - 1),
            int(xs.max()) + 2,
            int(ys.max()) + 2,
        ])
    return boxes


def box_iou(first, second):
    """The overlap of two boxes."""
    x1 = max(first[0], second[0])
    y1 = max(first[1], second[1])
    x2 = min(first[2], second[2])
    y2 = min(first[3], second[3])
    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    area_a = (first[2] - first[0]) * (first[3] - first[1])
    area_b = (second[2] - second[0]) * (second[3] - second[1])
    union = area_a + area_b - intersection
    return intersection / union if union else 0.0


def match_detections(detections, truths, iou_threshold=MATCH_IOU):
    """The detections that match a truth, and the ones that do not.

    A detection is matched to the truth it overlaps the most, and every
    detection is used at most once.
    """
    matched = set()
    true_positive = 0
    false_negative = 0

    for truth in truths:
        best = -1.0
        best_index = -1
        for index, detection in enumerate(detections):
            if index in matched:
                continue
            overlap = box_iou(truth, detection)
            if overlap > best:
                best = overlap
                best_index = index
        if best >= iou_threshold:
            true_positive += 1
            matched.add(best_index)
        else:
            false_negative += 1

    false_positive = len(detections) - len(matched)
    return {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
    }


def evaluate(scenes, lane_threshold=200, vehicle_threshold=175, iou_threshold=MATCH_IOU):
    """The metrics of the detector over a set of scenes."""
    lane_scores = []
    counts = {"true_positive": 0, "false_positive": 0, "false_negative": 0}

    for scene in scenes:
        predicted_lane = scene["image"] > lane_threshold
        lane_scores.append(lane_iou(predicted_lane, scene["lane_mask"]))

        detections = detect_vehicles(scene["image"], threshold=vehicle_threshold)
        matched = match_detections(detections, scene["boxes"], iou_threshold)
        for key in counts:
            counts[key] += matched[key]

    precision = counts["true_positive"] / max(1, counts["true_positive"] + counts["false_positive"])
    recall = counts["true_positive"] / max(1, counts["true_positive"] + counts["false_negative"])
    return {
        "lane_iou": round(float(np.mean(lane_scores)) if lane_scores else 0.0, 4),
        "vehicle_precision": round(float(precision), 4),
        "vehicle_recall": round(float(recall), 4),
        "scenes": len(scenes),
    }


def split_scenes(data, fraction=0.6):
    """The scenes the threshold is fitted on and the ones it is measured on."""
    scenes = data["scenes"]
    cut = max(1, int(len(scenes) * fraction))
    return scenes[:cut], scenes[cut:]


def train(data, quick=False):
    """Fit the lane threshold and measure the detector on the other scenes."""
    tuning, testing = split_scenes(data)

    best = None
    for threshold in LANE_THRESHOLDS:
        metrics = evaluate(tuning, lane_threshold=threshold)
        metrics["lane_threshold"] = threshold
        if best is None or metrics["lane_iou"] > best["lane_iou"]:
            best = metrics

    model = {"lane_threshold": best["lane_threshold"], "vehicle_threshold": 175}

    # The metrics are measured on the scenes the threshold was not chosen for.
    held_out = evaluate(testing, lane_threshold=best["lane_threshold"])
    return model, {
        "lane_iou": held_out["lane_iou"],
        "vehicle_precision": held_out["vehicle_precision"],
        "vehicle_recall": held_out["vehicle_recall"],
        "lane_threshold": best["lane_threshold"],
        "tuning_scenes": len(tuning),
        "test_scenes": held_out["scenes"],
    }


def demo(data):
    scene = data["scenes"][0]
    boxes = detect_vehicles(scene["image"])
    print(f"Lane pixels detected: {int((scene['image'] > 200).sum())}")
    print(f"Vehicle boxes: {boxes}")
    metrics = evaluate([scene])
    print(f"Scene lane IoU: {metrics['lane_iou']:.2f}")

    Path("artifacts").mkdir(exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(8, 4))
    axes[0].imshow(scene["image"], cmap="gray")
    axes[0].set_title("scene")
    axes[1].imshow(scene["image"] > 200, cmap="gray")
    axes[1].set_title("lane threshold")
    for axis in axes:
        axis.axis("off")
    fig.tight_layout()
    fig.savefig("artifacts/perception_demo.png", dpi=110)
    plt.close(fig)
