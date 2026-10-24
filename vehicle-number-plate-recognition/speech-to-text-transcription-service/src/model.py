"""Segment the waveform, classify each word, decode the sentence."""
import numpy as np
from sklearn.ensemble import RandomForestClassifier

from src.data import SAMPLE_RATE, features


def segment(signal, frame_size=160, threshold=0.015):
    count = len(signal) // frame_size
    energies = np.array([
        float(np.sqrt(np.mean(signal[index * frame_size:(index + 1) * frame_size] ** 2)))
        for index in range(count)
    ])
    active = energies > threshold
    segments = []
    start = None
    for index, value in enumerate(active):
        if value and start is None:
            start = index
        elif not value and start is not None:
            if index - start >= 8:
                segments.append(signal[start * frame_size:index * frame_size])
            start = None
    if start is not None:
        segments.append(signal[start * frame_size:])
    return segments


def transcribe(signal, model, vocabulary):
    words = []
    for part in segment(signal):
        prediction = model.predict(features(part).reshape(1, -1))[0]
        words.append(vocabulary[int(prediction)])
    return words


def train(data, quick=False):
    model = RandomForestClassifier(
        n_estimators=50 if quick else 160,
        max_depth=12,
        random_state=5,
    )
    model.fit(data["X"], data["y"])
    correct = 0
    total = 0
    for truth, signal in data["phrases"]:
        predicted = transcribe(signal, model, data["words"])
        total += len(truth)
        correct += sum(int(a == b) for a, b in zip(truth, predicted))
        correct -= abs(len(predicted) - len(truth))
    wer = 1 - max(0.0, correct / max(1, total))
    return model, {
        "word_error_rate": round(float(wer), 4),
        "vocabulary_size": len(data["words"]),
        "test_phrases": len(data["phrases"]),
        "sample_rate": SAMPLE_RATE,
    }


def demo(data):
    model, metrics = train(data, quick=True)
    truth, signal = data["phrases"][0]
    predicted = transcribe(signal, model, data["words"])
    print("Reference:", " ".join(truth))
    print("Predicted:", " ".join(predicted))
    print(f"Word error rate on the test phrases: {metrics['word_error_rate']:.3f}")
