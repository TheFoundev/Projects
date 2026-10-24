"""Synthetic spoken digits with pauses between words."""
import numpy as np

SAMPLE_RATE = 8000
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
TONES = {
    "zero": (520, 900), "one": (420, 1500), "two": (610, 1100), "three": (690, 1600),
    "four": (480, 1300), "five": (720, 1250), "six": (560, 1700), "seven": (640, 1450),
    "eight": (450, 1150), "nine": (750, 1800),
}


def tone(word, seed=0, duration=0.34):
    rng = np.random.default_rng(seed)
    first, second = TONES[word]
    time = np.arange(int(SAMPLE_RATE * duration)) / SAMPLE_RATE
    envelope = np.minimum(1, time / 0.03) * np.exp(-time * 2.0)
    signal = 0.55 * np.sin(2 * np.pi * first * time) + 0.3 * np.sin(2 * np.pi * second * time)
    signal = signal * envelope + rng.normal(0, 0.015, len(time))
    return (0.8 * signal / (np.max(np.abs(signal)) + 1e-9)).astype("float32")


def utterance(words, seed=0):
    parts = []
    for index, word in enumerate(words):
        parts.append(tone(word, seed + index))
        parts.append(np.zeros(int(SAMPLE_RATE * 0.12), dtype="float32"))
    return np.concatenate(parts)


def features(segment, frames=12, bands=8):
    frame_length = max(16, len(segment) // frames)
    window = np.hanning(frame_length)
    rows = []
    for index in range(frames):
        chunk = segment[index * frame_length:(index + 1) * frame_length]
        if len(chunk) < frame_length:
            chunk = np.pad(chunk, (0, frame_length - len(chunk)))
        spectrum = np.abs(np.fft.rfft(chunk * window)) ** 2
        edges = np.linspace(1, len(spectrum), bands + 1).astype(int)
        rows.append(np.log1p([spectrum[edges[i]:max(edges[i] + 1, edges[i + 1])].mean() for i in range(bands)]))
    return np.asarray(rows).reshape(-1)


def load_data(seed=42, quick=False):
    rng = np.random.default_rng(seed)
    per_word = 6 if quick else 14
    X, y = [], []
    for label, word in enumerate(WORDS):
        for sample in range(per_word):
            X.append(features(tone(word, seed + label * 100 + sample)))
            y.append(label)

    phrases = []
    for index in range(6 if quick else 16):
        words = [WORDS[int(value)] for value in rng.integers(0, len(WORDS), 3)]
        phrases.append((words, utterance(words, seed + 1000 + index)))
    return {"X": np.asarray(X), "y": np.asarray(y), "phrases": phrases, "words": WORDS}
