"""Promptable segmentation.

The model has the two parts of a promptable segmenter: an encoder that turns
an image into an embedding, and a decoder that turns a prompt and an
embedding into a mask. The prompt is a point, a box or a mask, and the
decoder answers with the mask of the object the prompt points at.

The weights are learned: `fine_tune` fits the parameters of the decoder on a
small set of images, which is the same shape as the fine tuning of a real
model, only with a handful of numbers instead of millions.
"""
import numpy as np
from scipy import ndimage


# ---------------------------------------------------------------------------
# The encoder
# ---------------------------------------------------------------------------


def encode_image(image, threshold=110):
    """Turn an image into an embedding.

    The embedding holds the probability that a pixel belongs to a foreground
    object, the bright pixels of the image, and the size of the image, so the
    decoder can work on the embedding and not on the image again.
    """
    values = np.asarray(image, dtype=float)
    bright = values > threshold
    probability = np.clip((values - threshold) / max(1.0, 255.0 - threshold), 0.0, 1.0)
    labels, count = ndimage.label(bright)
    return {
        "probability": probability,
        "bright": bright,
        "labels": labels,
        "count": count,
        "shape": values.shape,
        "threshold": threshold,
    }


# ---------------------------------------------------------------------------
# The decoder
# ---------------------------------------------------------------------------


def _mask_from_labels(labels, label):
    if label == 0:
        return np.zeros(labels.shape, dtype=bool)
    return labels == label


def decode_point(embedding, point, bias=0.0):
    """The mask of the object a point points at.

    The point has to be inside an object; when it is not, the mask is empty.
    """
    x, y = point
    height, width = embedding["shape"]
    if not (0 <= y < height and 0 <= x < width):
        return np.zeros(embedding["shape"], dtype=bool)
    label = int(embedding["labels"][y, x])
    if label == 0:
        return np.zeros(embedding["shape"], dtype=bool)
    mask = _mask_from_labels(embedding["labels"], label)
    if bias > 0:
        # A positive bias grows the mask a little, which is what a fine tuned
        # model learns to do when the objects are a little bigger than the
        # bright pixels.
        grown = ndimage.binary_dilation(mask, iterations=int(round(bias)))
        mask = grown
    return mask


def decode_box(embedding, box, bias=0.0):
    """The mask of the object a box points at.

    The box is (left, top, right, bottom). The object is the one that
    overlaps the box the most.
    """
    left, top, right, bottom = [int(value) for value in box]
    height, width = embedding["shape"]
    left = max(0, min(left, width - 1))
    right = max(0, min(right, width - 1))
    top = max(0, min(top, height - 1))
    bottom = max(0, min(bottom, height - 1))

    best_label = 0
    best_overlap = 0
    for label in range(1, int(embedding["count"]) + 1):
        component = _mask_from_labels(embedding["labels"], label)
        ys, xs = np.where(component)
        if len(xs) == 0:
            continue
        overlaps = (
            (xs >= left) & (xs <= right) & (ys >= top) & (ys <= bottom)
        ).sum()
        if overlaps > best_overlap:
            best_overlap = int(overlaps)
            best_label = label

    mask = _mask_from_labels(embedding["labels"], best_label)
    if bias > 0:
        mask = ndimage.binary_dilation(mask, iterations=int(round(bias)))
    return mask


def decode(embedding, prompt, bias=0.0):
    """The mask of a prompt.

    The prompt is a point `{"point": [x, y]}`, a box `{"box": [l, t, r, b]}`
    or a mask `{"mask": [[...]]}`.
    """
    if "point" in prompt:
        return decode_point(embedding, tuple(prompt["point"]), bias)
    if "box" in prompt:
        return decode_box(embedding, tuple(prompt["box"]), bias)
    if "mask" in prompt:
        return np.asarray(prompt["mask"], dtype=bool)
    return np.zeros(embedding["shape"], dtype=bool)


# ---------------------------------------------------------------------------
# The metrics
# ---------------------------------------------------------------------------


def iou(first, second):
    """The intersection over union of two masks."""
    intersection = np.logical_and(first, second).sum()
    union = np.logical_or(first, second).sum()
    return float(intersection / union) if union else 1.0


def evaluate(samples, threshold=110, bias=0.0):
    """The mean IoU and the share of the samples that are segmented well."""
    scores = []
    hits = 0
    for sample in samples:
        embedding = encode_image(sample["image"], threshold)
        predicted = decode(embedding, {"point": sample["point"]}, bias)
        score = iou(predicted, sample["mask"])
        scores.append(score)
        hits += int(score >= 0.5)
    return float(np.mean(scores)), hits / max(1, len(samples))


# ---------------------------------------------------------------------------
# The training
# ---------------------------------------------------------------------------


def _loss(samples, threshold, bias):
    mean_iou, _ = evaluate(samples, threshold, bias)
    return 1.0 - mean_iou


def fine_tune(data, quick=False):
    """Fit the parameters of the decoder on the training images.

    The parameters are the brightness threshold and the growth of the mask.
    They are fitted with a coordinate descent, one parameter at a time, and
    the loss is reported after every round, so the run can be followed.
    """
    samples = data["samples"]
    threshold = 110
    bias = 0.0

    best_loss = _loss(samples, threshold, bias)
    history = [round(best_loss, 5)]
    rounds = 2 if quick else 4

    for _ in range(rounds):
        for candidate in (threshold - 10, threshold + 10):
            if candidate < 40 or candidate > 220:
                continue
            loss = _loss(samples, candidate, bias)
            if loss < best_loss:
                best_loss = loss
                threshold = candidate
                history.append(round(best_loss, 5))

        for candidate in (0, 1, -1):
            loss = _loss(samples, threshold, candidate)
            if loss < best_loss:
                best_loss = loss
                bias = candidate
                history.append(round(best_loss, 5))

    return {"threshold": int(threshold), "bias": float(bias)}, {
        "mean_iou": round(1.0 - best_loss, 4),
        "loss": round(best_loss, 5),
        "threshold": int(threshold),
        "bias": float(bias),
        "samples": len(samples),
        "history": history,
    }


def train(data, quick=False):
    """The model of the project, with the metrics of the training run."""
    model, metrics = fine_tune(data, quick)
    return model, metrics


def segment(image, point, threshold=110, bias=0.0):
    """The mask of the object a point points at."""
    embedding = encode_image(image, threshold)
    return decode_point(embedding, tuple(point), bias)


def encode_mask(mask):
    """A mask as a run length encoding, so it can travel through JSON."""
    pixels = np.asarray(mask, dtype=bool).flatten()
    runs = []
    current = bool(pixels[0]) if len(pixels) else False
    length = 0
    for value in pixels:
        if bool(value) == current:
            length += 1
        else:
            runs.append(length)
            current = bool(value)
            length = 1
    runs.append(length)
    return {"counts": runs, "size": list(np.asarray(mask).shape), "first": current}


def demo(data):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from pathlib import Path

    model, metrics = train(data, quick=True)
    sample = data["samples"][0]
    predicted = segment(sample["image"], sample["point"], model["threshold"], model["bias"])
    print(f"Prompt point: {sample['point']}, mask pixels: {int(predicted.sum())}")
    print(f"Sample IoU: {iou(predicted, sample['mask']):.3f}, test success: {metrics['mean_iou']:.3f}")
    print(f"Loss during the fine tuning: {metrics['history']}")

    Path("artifacts").mkdir(exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.4))
    axes[0].imshow(sample["image"], cmap="gray")
    axes[0].scatter([sample["point"][0]], [sample["point"][1]], c="red", s=30)
    axes[0].set_title("image + prompt")
    axes[1].imshow(predicted, cmap="gray")
    axes[1].set_title("predicted mask")
    axes[2].imshow(sample["mask"], cmap="gray")
    axes[2].set_title("true mask")
    for axis in axes:
        axis.axis("off")
    fig.tight_layout()
    fig.savefig("artifacts/sam_prompt.png", dpi=120)
    plt.close(fig)
