"""Frame classifier and a greedy collapse decoder."""
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

from src.data import frame_features

def decode(frames, model):
    predictions = model.predict(frames)
    collapsed = []
    previous = None
    for value in predictions:
        value = int(value)
        if value != previous and value != 5:
            collapsed.append(value)
        previous = value
    return collapsed

def word_distance(truth, predicted):
    # Compare the frame-label sequence against a decoded sequence of the same length.
    return 1.0 if truth != predicted else 0.0

def train(data, quick=False):
    model = RandomForestClassifier(n_estimators=50 if quick else 160, max_depth=12, random_state=3)
    model.fit(data["X"], data["y"])
    frame_accuracy = accuracy_score(data["y"], model.predict(data["X"]))

    errors = 0
    total = 0
    for word, signal, labels in data["examples"]:
        predicted = decode(frame_features(signal), model)
        expected = [int(value) for value in labels if int(value) != 5]
        # Collapse expected labels in the same way for a fair comparison.
        expected_collapsed = []
        previous = None
        for value in expected:
            if value != previous:
                expected_collapsed.append(value)
            previous = value
        total += 1
        errors += int(predicted != expected_collapsed)
    return model, {
        "frame_accuracy": round(float(frame_accuracy), 4),
        "word_error_rate": round(float(errors / max(1, total)), 4),
        "words": len(data["words"]),
        "frames": int(len(data["y"])),
    }

def demo(data):
    model, metrics = train(data, quick=True)
    word, signal, _ = data["examples"][0]
    decoded = decode(frame_features(signal), model)
    print(f"Reference word: {word}")
    print(f"Decoded phoneme ids: {decoded}")
    print(f"Frame accuracy: {metrics['frame_accuracy']:.3f}, word error rate: {metrics['word_error_rate']:.3f}")
