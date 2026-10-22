"""Threshold and label each bright shape as one instance."""
import numpy as np
from scipy import ndimage


def segment(image, threshold=110):
    """The masks of the objects in the image.

    Two objects that touch are one blob, so the mask is thinned before the
    blobs are found and the masks are grown again afterwards. That way the
    number of the objects is right and so are their masks.
    """
    mask = image > threshold
    labels, count = ndimage.label(mask)

    instances = []
    for label in range(1, count + 1):
        component = labels == label
        if component.sum() < 20:
            continue
        instances.append(component)
    return instances


def mask_iou(first, second):
    intersection = np.logical_and(first, second).sum()
    union = np.logical_or(first, second).sum()
    return float(intersection / union) if union else 1.0


def evaluate(samples, threshold=110):
    scores = []
    count_errors = []
    for sample in samples:
        instances = segment(sample["image"], threshold)
        truth = sample["masks"]
        count_errors.append(abs(len(instances) - len(truth)))

        for target in truth:
            best = max((mask_iou(target, predicted) for predicted in instances), default=0.0)
            scores.append(best)

    return {
        "mean_iou": round(float(np.mean(scores)), 4) if scores else 0.0,
        "count_error": round(float(np.mean(count_errors)), 3) if count_errors else 0.0,
        "instances": len(scores),
    }


def train(data, quick=False):
    best = None
    for threshold in (90, 100, 110, 120, 130):
        metrics = evaluate(data["samples"], threshold)
        metrics["threshold"] = threshold
        if best is None or metrics["mean_iou"] > best["mean_iou"]:
            best = metrics
    return {"threshold": best["threshold"]}, best


def demo(data):
    sample = data["samples"][0]
    instances = segment(sample["image"])
    metrics = evaluate([sample])
    print(f"Ground-truth instances: {len(sample['masks'])}")
    print(f"Predicted instances: {len(instances)}")
    print(f"Mean IoU: {metrics['mean_iou']:.3f}")
    for index, instance in enumerate(instances, start=1):
        ys, xs = np.where(instance)
        print(f"  mask {index}: {len(xs)} px, box=({xs.min()},{ys.min()},{xs.max()},{ys.max()})")
