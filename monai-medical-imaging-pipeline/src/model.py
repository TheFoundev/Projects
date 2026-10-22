"""Percentile segmentation and a two-feature patient classifier."""
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score


def dice(predicted, truth):
    intersection = np.logical_and(predicted, truth).sum()
    total = predicted.sum() + truth.sum()
    return float(2 * intersection / total) if total else 1.0


def segment(volume, percentile=94):
    threshold = float(np.percentile(volume, percentile))
    return volume >= threshold


def volume_features(volume, mask):
    lesion = volume[mask] if mask.any() else np.array([0.0])
    return [float(mask.sum()), float(np.mean(lesion)), float(np.std(volume))]


def train(data, quick=False):
    best = None
    for percentile in (90, 92, 94, 96):
        scores = [dice(segment(volume, percentile), mask) for volume, mask, _ in data["train"]]
        score = float(np.mean(scores))
        if best is None or score > best[0]:
            best = (score, percentile)

    percentile = best[1]
    train_features = [volume_features(volume, segment(volume, percentile)) for volume, _, _ in data["train"]]
    train_labels = [label for _, _, label in data["train"]]
    model = LogisticRegression(max_iter=300)
    model.fit(np.asarray(train_features), np.asarray(train_labels))

    test_dice = [dice(segment(volume, percentile), mask) for volume, mask, _ in data["test"]]
    test_features = [volume_features(volume, segment(volume, percentile)) for volume, _, _ in data["test"]]
    test_labels = [label for _, _, label in data["test"]]
    prediction = model.predict(np.asarray(test_features))
    return {"segmentation_percentile": percentile, "classifier": model}, {
        "mean_dice": round(float(np.mean(test_dice)), 4),
        "classification_accuracy": round(float(accuracy_score(test_labels, prediction)), 4),
        "threshold_percentile": percentile,
        "test_volumes": len(data["test"]),
    }


def demo(data):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from pathlib import Path

    model, metrics = train(data, quick=True)
    volume, mask, label = data["sample"]
    predicted = segment(volume, metrics["threshold_percentile"])
    print(f"True label: {label}, predicted lesion voxels: {int(predicted.sum())}")
    print(f"Sample Dice: {dice(predicted, mask):.3f}")
    print(f"Test mean Dice: {metrics['mean_dice']:.3f}, classification accuracy: {metrics['classification_accuracy']:.3f}")

    middle = volume.shape[0] // 2
    Path("artifacts").mkdir(exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(9, 3))
    axes[0].imshow(volume[middle], cmap="gray")
    axes[0].set_title("slice")
    axes[1].imshow(mask[middle], cmap="gray")
    axes[1].set_title("truth")
    axes[2].imshow(predicted[middle], cmap="gray")
    axes[2].set_title("threshold")
    for axis in axes:
        axis.axis("off")
    fig.tight_layout()
    fig.savefig("artifacts/medical_slices.png", dpi=110)
    plt.close(fig)
