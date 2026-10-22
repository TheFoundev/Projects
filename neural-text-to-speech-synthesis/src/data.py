"""The corpus of the project and the pronunciation table.

The corpus is a list of English phrases with the duration a speaker would
need for them. The duration follows the usual rule of thumb: a word costs
about 140 ms and a syllable about 85 ms, which is what the duration model of
:mod:`src.duration` is fitted on.
"""

from __future__ import annotations

#: The phrases of the corpus.
PHRASES = [
    "hello world",
    "good morning",
    "the quick brown fox",
    "system ready",
    "please try again",
    "the message broker is ready",
    "orders are processed in order",
    "a retry is published to the next queue",
    "the dead letter queue keeps the failed orders",
    "every order has an idempotency key",
    "the consumer acknowledges a delivery once",
    "the publisher waits for the broker confirmation",
    "backpressure is bounded by the prefetch window",
    "the topology is declared when the broker is up",
    "a connection that is lost is opened again",
    "metrics are exposed in the prometheus format",
    "the http interface answers the health route",
    "the burst generator sends many orders at once",
    "the pipeline validates reserves charges and fulfils",
    "an invalid order is dead lettered at once",
    "a transient failure is retried with a delay",
    "the pipeline runs four steps for every order",
    "the service reads the payload and settles it",
    "the consumer subscribes to the process queue",
    "the exchange routes the orders by their key",
    "the latency of a delivery is measured in seconds",
    "the queue is a quorum queue with a delivery limit",
    "the confirmation of the publisher has a timeout",
    "the seen cache drops the duplicated orders",
    "the connection reports whether it is blocked",
    "the application starts the http interface",
    "the topology is idempotent and can be repeated",
    "the payload of a message is a json order",
    "the amount of an order must be positive",
    "the currency of an order must be known",
    "the items of an order need a quantity",
    "a warehouse that is down is retried",
    "the payment gateway may time out",
    "the stock of a sku is limited",
    "the fingerprint of an order is stable",
    "the key of an order never changes",
    "the text of a phrase becomes phonemes",
    "the phonemes become a waveform",
    "the waveform is written to a wav file",
]

def syllable_count(word: str) -> int:
    """The number of syllables of a word (at least one)."""
    return max(1, sum(character in "aeiouy" for character in word.lower()))


def phrase_syllables(phrase: str) -> int:
    """The number of syllables of a phrase."""
    return sum(syllable_count(word) for word in phrase.split())


def target_duration(phrase: str) -> float:
    """The duration a speaker needs for a phrase, in seconds."""
    words = phrase.split()
    return 0.14 * len(words) + 0.085 * phrase_syllables(phrase)


def build_rows(phrases: list[str]) -> list[tuple[str, int, int, float]]:
    """The rows of the corpus: ``(phrase, length, syllables, duration)``."""
    return [
        (phrase, len(phrase), phrase_syllables(phrase), target_duration(phrase))
        for phrase in phrases
    ]


def load_data(seed: int = 42, quick: bool = False) -> dict:
    """The corpus and the settings of the project.

    ``quick`` keeps only the first three phrases, which is what the smoke
    test uses.
    """
    phrases = PHRASES[:3] if quick else PHRASES
    rows = build_rows(phrases)
    return {
        "phrases": phrases,
        "rows": rows,
        "sample_rate": 16000,
        "seed": seed,
    }
