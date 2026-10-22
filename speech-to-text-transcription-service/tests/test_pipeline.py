"""Tests for the transcription."""
import numpy as np

from src.data import load_data
from src.model import demo, segment, train, transcribe


def test_pipeline_runs(capsys):
    data = load_data(seed=1, quick=True)
    assert data is not None

    model, metrics = train(data, quick=True)
    assert model is not None
    assert isinstance(metrics, dict) and metrics

    for value in metrics.values():
        if isinstance(value, bool):
            continue
        assert value is None or isinstance(value, (int, float, str))

    demo(data)
    assert capsys.readouterr().out.strip()


def test_seed_is_usable():
    first = load_data(seed=3, quick=True)
    second = load_data(seed=3, quick=True)
    assert first.keys() == second.keys()


def test_the_signal_is_split_into_words():
    data = load_data(seed=3, quick=True)
    _, signal = data["phrases"][0]
    segments = segment(signal)
    assert len(segments) >= 1


def test_the_words_are_transcribed():
    data = load_data(seed=3, quick=True)
    model, _ = train(data, quick=True)
    truth, signal = data["phrases"][0]
    predicted = transcribe(signal, model, data["words"])
    assert len(predicted) == len(truth)


def test_the_error_rate_is_a_share():
    data = load_data(seed=4, quick=True)
    _, metrics = train(data, quick=True)
    assert metrics["word_error_rate"] >= 0
    assert metrics["vocabulary_size"] == len(data["words"])
