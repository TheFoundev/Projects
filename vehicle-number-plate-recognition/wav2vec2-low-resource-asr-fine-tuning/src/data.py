"""Synthetic phoneme sequences and frame features."""
import numpy as np

SAMPLE_RATE = 8000
WORDS = ["alpha", "bravo", "cobalt", "delta", "ember", "fjord"]
PHONEMES = [(350, 700), (420, 980), (520, 1200), (610, 1450), (700, 1650)]

def word_signal(word, seed=0):
    rng = np.random.default_rng(seed)
    indices = [WORDS.index(word) % len(PHONEMES)]
    for _ in range(3):
        indices.append(int(rng.integers(0, len(PHONEMES))))
    parts = []
    labels = []
    for phoneme_index in indices:
        first, second = PHONEMES[phoneme_index]
        time = np.arange(int(SAMPLE_RATE * 0.09)) / SAMPLE_RATE
        envelope = np.sin(np.linspace(0, np.pi, len(time))) ** 0.5
        parts.append((0.5 * np.sin(2 * np.pi * first * time) + 0.3 * np.sin(2 * np.pi * second * time)) * envelope)
        labels.extend([phoneme_index] * 4)
        parts.append(np.zeros(int(SAMPLE_RATE * 0.015)))
        labels.extend([len(PHONEMES)] * 1)
    signal = np.concatenate(parts) + rng.normal(0, 0.015, sum(len(part) for part in parts))
    return signal / (np.max(np.abs(signal)) + 1e-9), np.asarray(labels[:16])

def frame_features(signal, frames=16, bands=10):
    length = max(16, len(signal) // frames)
    window = np.hanning(length)
    rows = []
    for index in range(frames):
        chunk = signal[index * length:(index + 1) * length]
        if len(chunk) < length:
            chunk = np.pad(chunk, (0, length - len(chunk)))
        spectrum = np.abs(np.fft.rfft(chunk * window)) ** 2
        edges = np.linspace(1, len(spectrum), bands + 1).astype(int)
        rows.append(np.log1p([spectrum[edges[i]:max(edges[i] + 1, edges[i + 1])].mean() for i in range(bands)]))
    return np.asarray(rows)

def load_data(seed=42, quick=False):
    per_word = 6 if quick else 18
    X, y = [], []
    examples = []
    for word_index, word in enumerate(WORDS):
        for sample in range(per_word):
            signal, labels = word_signal(word, seed + word_index * 100 + sample)
            matrix = frame_features(signal)
            X.extend(matrix)
            y.extend(labels)
            examples.append((word, signal, labels))
    return {
        "X": np.asarray(X),
        "y": np.asarray(y),
        "examples": examples,
        "words": WORDS,
        "blank": len(PHONEMES),
    }
