"""PCA reconstruction error as an anomaly score."""
import numpy as np
from sklearn.decomposition import PCA
from sklearn.metrics import precision_score, recall_score, roc_auc_score


def flatten(patches):
    return np.asarray(patches).reshape(len(patches), -1) / 255.0


def reconstruction_scores(model, patches):
    matrix = flatten(patches)
    rebuilt = model.inverse_transform(model.transform(matrix))
    return np.mean((matrix - rebuilt) ** 2, axis=1)


def train(data, quick=False):
    clean = flatten(data["clean_train"])
    components = max(1, min(8, clean.shape[0], clean.shape[1]))
    model = PCA(n_components=components, random_state=1)
    model.fit(clean)

    train_scores = reconstruction_scores(model, data["clean_train"])
    threshold = float(np.quantile(train_scores, 0.95))
    scores = reconstruction_scores(model, data["X_test"])
    predictions = (scores > threshold).astype(int)

    if len(np.unique(data["y_test"])) > 1:
        auc = roc_auc_score(data["y_test"], scores)
    else:
        auc = 0.5
    return {"pca": model, "threshold": threshold}, {
        "roc_auc": round(float(auc), 4),
        "precision": round(float(precision_score(data["y_test"], predictions, zero_division=0)), 4),
        "recall": round(float(recall_score(data["y_test"], predictions, zero_division=0)), 4),
        "threshold": round(threshold, 6),
        "test_patches": int(len(data["y_test"])),
    }


def demo(data):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from pathlib import Path

    model, metrics = train(data, quick=True)
    scores = reconstruction_scores(model["pca"], data["X_test"])
    print(f"Threshold: {metrics['threshold']:.6f}")
    print(f"Test AUC: {metrics['roc_auc']:.3f}, recall: {metrics['recall']:.3f}")
    print(f"Top anomaly score: {scores.max():.6f}")

    Path("artifacts").mkdir(exist_ok=True)
    fig, axes = plt.subplots(1, 4, figsize=(8, 2.4))
    for axis, patch, mask in zip(axes, data["samples"][:4], data["masks"][:4]):
        axis.imshow(patch, cmap="gray")
        if mask.any():
            axis.contour(mask, colors="red", linewidths=0.7)
        axis.axis("off")
    fig.tight_layout()
    fig.savefig("artifacts/defect_samples.png", dpi=110)
    plt.close(fig)
