"""Four detectors with a shared ROC AUC evaluation."""
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import roc_auc_score
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM


def zscore_scores(X):
    centered = X - X.mean(axis=0)
    covariance = np.cov(centered, rowvar=False) + np.eye(X.shape[1]) * 1e-6
    inverse = np.linalg.inv(covariance)
    return np.einsum("ij,jk,ik->i", centered, inverse, centered)


def train(data, quick=False):
    scores = {}
    for name, (X, y) in data["datasets"].items():
        normal = X[y == 0]
        row = {}
        row["zscore"] = zscore_scores(X)

        forest = IsolationForest(n_estimators=60 if quick else 160, contamination=0.1, random_state=2)
        forest.fit(normal)
        row["isolation_forest"] = -forest.score_samples(X)

        lof = LocalOutlierFactor(n_neighbors=15, novelty=True, contamination=0.1)
        lof.fit(normal)
        row["lof"] = -lof.score_samples(X)

        svm = OneClassSVM(nu=0.1, gamma="scale")
        svm.fit(normal)
        row["one_class_svm"] = -svm.score_samples(X)

        scores[name] = {detector: round(float(roc_auc_score(y, values)), 4) for detector, values in row.items()}

    flattened = {
        detector: float(np.mean([scores[name][detector] for name in scores]))
        for detector in next(iter(scores.values()))
    }
    best = max(flattened, key=flattened.get)
    return {"scores": scores}, {
        "best_detector": best,
        "best_mean_auc": round(flattened[best], 4),
        "detectors": len(flattened),
        "datasets": len(scores),
    }


def demo(data):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from pathlib import Path

    _, metrics = train(data, quick=True)
    print(f"Best detector: {metrics['best_detector']} (mean AUC {metrics['best_mean_auc']:.3f})")
    for name, (X, y) in data["datasets"].items():
        print(f"  {name:10s} n={len(X)} outliers={int(y.sum())}")

    Path("artifacts").mkdir(exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.2))
    for axis, (name, (X, y)) in zip(axes, data["datasets"].items()):
        axis.scatter(X[y == 0, 0], X[y == 0, 1], s=8, c="#3b82f6")
        axis.scatter(X[y == 1, 0], X[y == 1, 1], s=16, c="#dc2626")
        axis.set_title(name)
    fig.tight_layout()
    fig.savefig("artifacts/outlier_datasets.png", dpi=110)
    plt.close(fig)
