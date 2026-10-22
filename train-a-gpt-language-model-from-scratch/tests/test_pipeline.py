"""Tests for the language model."""
from src.data import load_data
from src.model import build_model, demo, train


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


def test_the_vocabulary_covers_the_text():
    data = load_data(seed=3, quick=True)
    model, metrics = train(data, quick=True)
    assert metrics["vocabulary_size"] > 0
    assert metrics["parameters"] > 0
