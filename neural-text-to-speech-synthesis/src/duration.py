"""The duration model: how long a word lasts and how it is shared.

The word level model is a linear regression over the number of characters and
the number of syllables, fitted on the corpus of :mod:`src.data`. The
syllable and phoneme level durations are derived from that prediction with
the weights of :mod:`src.prosody`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.linear_model import LinearRegression

from src.g2p import Word
from src.prosody import Prosody, phoneme_durations, syllable_durations


@dataclass
class DurationModel:
    """Predicts the duration of a word and of every phoneme in it."""

    regression: LinearRegression
    #: The mean absolute error of the regression on its training data.
    mae: float
    #: The mean duration of a syllable in the training data, in seconds.
    mean_syllable: float

    def predict_word(self, length: int, syllables: int) -> float:
        """The duration of a word, in seconds."""
        prediction = float(self.regression.predict([[length, syllables]])[0])
        return max(0.05, prediction)

    def predict(self, word: Word, prosody: Prosody) -> list[float]:
        """The duration of every phoneme of a word, in seconds."""
        if not word.phones:
            return []
        total = self.predict_word(len(word.text), word.syllable_count)
        result: list[float] = []
        syllables = syllable_durations(word, total, prosody)
        offset = 0
        from src.g2p import word_to_syllables

        for syllable, duration in zip(word_to_syllables(word), syllables):
            result.extend(phoneme_durations(syllable, duration))
            offset += len(syllable)
        # The phonemes that are not in a syllable (a word without a vowel)
        # share what is left of the word.
        if len(result) < len(word.phones):
            missing = len(word.phones) - len(result)
            result.extend([total / max(1, len(word.phones))] * missing)
        return result


def fit(rows: list[tuple[str, int, int, float]]) -> DurationModel:
    """Fit the duration model on the rows of the corpus.

    A row is ``(phrase, length, syllables, duration)``.
    """
    if not rows:
        raise ValueError("the duration model needs at least one sample")
    features = np.array([[length, syllables] for _, length, syllables, _ in rows], dtype=float)
    targets = np.array([duration for *_, duration in rows], dtype=float)
    regression = LinearRegression().fit(features, targets)
    prediction = regression.predict(features)
    mae = float(np.mean(np.abs(prediction - targets)))
    mean_syllable = float(np.mean(targets / np.maximum(features[:, 1], 1)))
    return DurationModel(regression=regression, mae=mae, mean_syllable=mean_syllable)
