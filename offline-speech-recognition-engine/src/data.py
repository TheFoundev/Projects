"""Synthesize command words and extract frame features."""
import numpy as np

WORDS = ["yes", "no", "start", "stop", "left", "right", "up", "down"]
SAMPLE_RATE = 8000
TONE_PAIRS = {
    "yes": (420, 900), "no": (520, 760), "start": (610, 1120), "stop": (480, 1040),
    "left": (700, 1500), "right": (640, 1320), "up": (760, 1700), "down": (390, 980),
}


def synthesize(word, seed=0):
    rng = np.random.default_rng(seed)
    first, second = TONE_PAIRS[word]
    duration = 0.40 + 0.03 * len(word)
    time = np.arange(int(SAMPLE_RATE * duration)) / SAMPLE_RATE
    envelope = np.minimum(1, time / 0.03) * np.exp(-time * 2.0)
    signal = (
        0.5 * np.sin(2 * np.pi * first * time)
        + 0.32 * np.sin(2 * np.pi * second * time)
        + 0.12 * np.sin(2 * np.pi * second * 1.7 * time)
    )
    signal = signal * envelope + rng.normal(0, 0.02, len(time))
    return signal / (np.max(np.abs(signal)) + 1e-9)


def frame_features(signal, frames=16, bands=8):
    length = max(16, len(signal) // frames)
    window = np.hanning(length)
    rows = []
    for index in range(frames):
        chunk = signal[index * length:(index + 1) * length]
        if len(chunk) < length:
            chunk = np.pad(chunk, (0, length - len(chunk)))
        spectrum = np.abs(np.fft.rfft(chunk * window)) ** 2
        edges = np.linspace(1, len(spectrum), bands + 1).astype(int)
        row = [spectrum[edges[i]:max(edges[i] + 1, edges[i + 1])].mean() for i in range(bands)]
        rows.append(np.log1p(row))
    matrix = np.asarray(rows)
    matrix = (matrix - matrix.mean()) / (matrix.std() + 1e-6)
    return matrix


def load_data(seed=42, quick=False):
    per_word = 5 if quick else 12
    train, test = [], []
    for word_index, word in enumerate(WORDS):
        for sample in range(per_word):
            features = frame_features(synthesize(word, seed + word_index * 100 + sample))
            if sample < per_word * 0.6:
                train.append((word, features))
            else:
                test.append((word, features))
    return {"train": train, "test": test, "words": WORDS}
