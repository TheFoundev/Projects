"""The prosody of a phrase: the pitch contour and the syllable weighting.

The model is simple but explicit:

* the fundamental frequency starts at a base value and **declines** over the
  phrase (the natural drift of a statement),
* a question lifts the last syllable instead of lowering it,
* a stressed syllable gets a local accent and is a little longer,
* the length of a syllable grows with the number of phonemes it holds.

Everything is deterministic, so the same phrase always sounds the same.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from src.g2p import KIND_WEIGHT, VOWELS, Word, word_to_syllables


@dataclass(frozen=True)
class Prosody:
    """The prosody of a phrase."""

    #: The fundamental frequency at the start of the phrase, in Hz.
    base_pitch: float = 120.0
    #: How much the pitch falls over the whole phrase, in Hz.
    declination: float = 18.0
    #: The relative height of a stressed syllable, as a factor.
    stress_accent: float = 1.25
    #: The relative length of a stressed syllable, as a factor.
    stress_length: float = 1.3
    #: True when the phrase is a question.
    question: bool = False

    def is_question(self, text: str) -> bool:
        """Does the text ask a question?"""
        stripped = text.strip()
        return stripped.endswith("?")

    def with_text(self, text: str) -> "Prosody":
        """The prosody of a phrase, taking the punctuation into account."""
        return Prosody(
            base_pitch=self.base_pitch,
            declination=self.declination,
            stress_accent=self.stress_accent,
            stress_length=self.stress_length,
            question=self.is_question(text),
        )

    def pitch_at(self, position: float, total: float) -> float:
        """The pitch in Hz at a relative position (0 at the start, 1 at the end)."""
        if total <= 0:
            return self.base_pitch
        ratio = min(1.0, max(0.0, position / total))
        pitch = self.base_pitch - self.declination * ratio
        if self.question and ratio > 0.8:
            # The last fifth of a question rises.
            pitch += self.declination * 1.6 * ((ratio - 0.8) / 0.2)
        return pitch


def syllable_weight(syllable: list[str]) -> float:
    """How heavy a syllable is, used to share the time of a word."""
    if not syllable:
        return 1.0
    total = sum(KIND_WEIGHT.get(_kind(phone), 0.5) for phone in syllable)
    return max(total, 0.5)


def _kind(phone: str) -> str:
    from src.g2p import kind_of

    return kind_of(phone)


def syllable_durations(word: Word, word_duration: float, prosody: Prosody) -> list[float]:
    """The duration of every syllable of a word, in seconds."""
    syllables = word_to_syllables(word)
    if not syllables:
        return []
    weights = [syllable_weight(syllable) for syllable in syllables]
    stressed = _stressed_syllable(word, syllables)
    if stressed is not None and 0 <= stressed < len(weights):
        weights[stressed] *= prosody.stress_length
    total = sum(weights)
    return [word_duration * weight / total for weight in weights]


def _stressed_syllable(word: Word, syllables: list[list[str]]) -> int | None:
    """The index of the syllable that carries the primary stress."""
    if not syllables:
        return None
    offset = 0
    for index, syllable in enumerate(syllables):
        if offset <= word.stress_index < offset + len(syllable):
            return index
        offset += len(syllable)
    return 0


def phoneme_durations(syllable: list[str], syllable_duration: float) -> list[float]:
    """Share the duration of a syllable among its phonemes."""
    if not syllable:
        return []
    weights = [KIND_WEIGHT.get(_kind(phone), 0.5) for phone in syllable]
    total = sum(weights)
    return [syllable_duration * weight / total for weight in weights]


def pitch_curve(duration: float, prosody: Prosody, accent_at: float | None = None) -> list[float]:
    """The pitch in Hz over a segment of the given duration."""
    if duration <= 0:
        return []
    steps = max(2, int(duration * 200))
    curve = []
    for index in range(steps):
        position = duration * index / steps
        pitch = prosody.pitch_at(position, duration)
        if accent_at is not None:
            distance = abs(position - accent_at)
            if distance < duration / 4:
                pitch *= prosody.stress_accent
        curve.append(pitch)
    return curve


def phrase_is_interrogative(text: str) -> bool:
    """True when the phrase ends with a question mark."""
    return text.strip().endswith("?")


def vibrato(pitch: float, position: float, depth: float = 0.01, rate: float = 5.0) -> float:
    """A small pitch modulation, so the voice does not sound like a beep."""
    return pitch * (1.0 + depth * math.sin(2 * math.pi * rate * position))
