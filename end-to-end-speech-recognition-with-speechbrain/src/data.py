"""Synthesize short spoken-digit-like signals and turn them into features."""
import numpy as np
from scipy.fftpack import dct

SAMPLE_RATE = 8000
DIGITS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]

# Two rough formant frequencies per digit, plus a duration offset.
VOICES = {
    "zero": (520, 900, 0.46),
    "one": (420, 1500, 0.32),
    "two": (610, 1100, 0.38),
    "three": (690, 1600, 0.42),
    "four": (480, 1300, 0.36),
    "five": (720, 1250, 0.34),
    "six": (560, 1700, 0.40),
    "seven": (640, 1450, 0.48),
    "eight": (450, 1150, 0.44),
    "nine": (750, 1800, 0.37),
}


def synthesize(word, seed=0, noise=0.02):
    rng = np.random.default_rng(seed)
    first, second, duration = VOICES[word]
    time = np.arange(int(SAMPLE_RATE * duration)) / SAMPLE_RATE
    envelope = np.minimum(1, time / 0.04) * np.exp(-time * 2.2)
    signal = (
        0.55 * np.sin(2 * np.pi * first * time)
        + 0.30 * np.sin(2 * np.pi * second * time)
        + 0.10 * np.sin(2 * np.pi * (first * 2) * time)
    )
    signal = signal * envelope
    signal = signal / (np.max(np.abs(signal)) + 1e-9)
    signal = signal + rng.normal(0, noise, len(signal))
    return signal


def features(signal, frames=20, bands=12):
    frame_length = max(16, len(signal) // frames)
    rows = []
    window = np.hanning(frame_length)
    for index in range(frames):
        start = index * frame_length
        chunk = signal[start:start + frame_length]
        if len(chunk) < frame_length:
            chunk = np.pad(chunk, (0, frame_length - len(chunk)))
        spectrum = np.abs(np.fft.rfft(chunk * window)) ** 2
        edges = np.linspace(1, len(spectrum), bands + 1).astype(int)
        energies = [spectrum[edges[i]:max(edges[i] + 1, edges[i + 1])].mean() for i in range(bands)]
        rows.append(np.log1p(energies))
    matrix = np.asarray(rows)
    cepstra = dct(matrix, type=2, axis=1, norm="ortho")[:, :bands]
    return cepstra.reshape(-1)


def load_data(seed=42, quick=False):
    rng = np.random.default_rng(seed)
    per_digit = 8 if quick else 24
    X_train, y_train, X_test, y_test = [], [], [], []
    for label, word in enumerate(DIGITS):
        for sample in range(per_digit):
            signal = synthesize(word, seed + label * 100 + sample)
            vector = features(signal)
            if sample < per_digit * 0.7:
                X_train.append(vector)
                y_train.append(label)
            else:
                X_test.append(vector)
                y_test.append(label)
    return {
        "X_train": np.asarray(X_train),
        "y_train": np.asarray(y_train),
        "X_test": np.asarray(X_test),
        "y_test": np.asarray(y_test),
        "labels": DIGITS,
        "seed": seed,
    }
