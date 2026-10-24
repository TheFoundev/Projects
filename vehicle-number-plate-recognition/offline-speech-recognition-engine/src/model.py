"""DTW nearest-template classifier."""
import numpy as np


def dtw_distance(first, second, band=None):
    """The distance between two sequences.

    The band is the Sakoe-Chiba band: only the paths that stay within a
    window of the diagonal are followed. Without it the distance of a long
    sequence is slow and the match can drift away from the right place.
    """
    n, m = len(first), len(second)
    if n == 0 or m == 0:
        return float("inf")
    if band is None:
        band = max(n, m)

    cost = np.full((n + 1, m + 1), np.inf)
    cost[0, 0] = 0
    for i in range(1, n + 1):
        # The window of the band follows the diagonal.
        start = max(1, i - band)
        end = min(m, i + band)
        for j in range(start, end + 1):
            distance = np.linalg.norm(first[i - 1] - second[j - 1])
            cost[i, j] = distance + min(cost[i - 1, j], cost[i, j - 1], cost[i - 1, j - 1])
    return float(cost[n, m] / (n + m))


def train(data, quick=False):
    templates = {}
    for word, features in data["train"]:
        templates.setdefault(word, []).append(features)

    averaged = {}
    for word, sequences in templates.items():
        # Use the shortest sequence as the reference to keep DTW cheap.
        averaged[word] = min(sequences, key=len)

    correct = 0
    for word, features in data["test"]:
        distances = {candidate: dtw_distance(features, template) for candidate, template in averaged.items()}
        prediction = min(distances, key=distances.get)
        correct += int(prediction == word)

    return {"templates": averaged}, {
        "accuracy": round(correct / max(1, len(data["test"])), 4),
        "vocabulary_size": len(averaged),
        "test_samples": len(data["test"]),
    }


def demo(data):
    from src.data import frame_features, synthesize

    model, metrics = train(data, quick=True)
    unknown = frame_features(synthesize("left", seed=9999))
    distances = {word: dtw_distance(unknown, template) for word, template in model["templates"].items()}
    ranked = sorted(distances.items(), key=lambda pair: pair[1])
    print("Spoken word: left")
    print("Closest templates:", [(word, round(score, 4)) for word, score in ranked[:3]])
    print(f"Test accuracy: {metrics['accuracy']:.3f}")
