"""Online EWMA with a rolling z-score."""
import numpy as np


def simulate(values, alpha=0.08, threshold=3.2, warmup=20):
    mean = float(values[0])
    variance = 1.0
    scores = np.zeros(len(values))
    flags = np.zeros(len(values), dtype=int)

    for index, value in enumerate(values):
        difference = value - mean
        mean += alpha * difference
        variance = (1 - alpha) * (variance + alpha * difference ** 2)
        scores[index] = abs(difference) / (np.sqrt(variance) + 1e-6)
        if index >= warmup and scores[index] > threshold:
            flags[index] = 1
    return scores, flags


def evaluate(labels, flags):
    true_positive = int(np.logical_and(labels == 1, flags == 1).sum())
    false_positive = int(np.logical_and(labels == 0, flags == 1).sum())
    false_negative = int(np.logical_and(labels == 1, flags == 0).sum())
    precision = true_positive / max(1, true_positive + false_positive)
    recall = true_positive / max(1, true_positive + false_negative)
    f1 = 2 * precision * recall / max(1e-9, precision + recall)
    return float(precision), float(recall), float(f1)


def train(data, quick=False):
    best = None
    for threshold in (2.4, 2.8, 3.2, 3.6, 4.0):
        _, flags = simulate(data["values"], threshold=threshold)
        precision, recall, f1 = evaluate(data["labels"], flags)
        if best is None or f1 > best[3]:
            best = (threshold, precision, recall, f1)
    return {"alpha": 0.08, "threshold": best[0]}, {
        "precision": round(best[1], 4),
        "recall": round(best[2], 4),
        "f1": round(best[3], 4),
        "threshold": best[0],
        "anomaly_points": int(data["labels"].sum()),
    }


def demo(data):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from pathlib import Path

    model, metrics = train(data, quick=True)
    scores, flags = simulate(data["values"], threshold=model["threshold"])
    print(f"Threshold: {model['threshold']}, F1: {metrics['f1']:.2f}")
    print(f"Flagged points: {int(flags.sum())}, true anomaly points: {metrics['anomaly_points']}")

    Path("artifacts").mkdir(exist_ok=True)
    fig, axes = plt.subplots(2, 1, figsize=(9, 5), sharex=True)
    axes[0].plot(data["timestamps"], data["values"], color="#334155", linewidth=0.8)
    axes[0].scatter(data["timestamps"][data["labels"] == 1], data["values"][data["labels"] == 1], c="#dc2626", s=12)
    axes[1].plot(data["timestamps"], scores, color="#7c3aed", linewidth=0.8)
    axes[1].axhline(model["threshold"], color="#dc2626", linestyle="--", linewidth=0.8)
    fig.tight_layout()
    fig.savefig("artifacts/stream_anomalies.png", dpi=110)
    plt.close(fig)
