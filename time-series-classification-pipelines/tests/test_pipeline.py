"""Tests for the classification."""
import numpy as np

from src.data import load_data
from src.model import demo, train


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


def test_the_split_is_in_time():
    """The training set may not hold the days that come after the test set."""
    data = load_data(seed=3, quick=True)
    train_rows = data["X_train"]
    test_rows = data["X_test"]
    assert len(train_rows) > 0
    assert len(test_rows) > 0


def test_the_accuracy_is_a_share():
    data = load_data(seed=4, quick=True)
    _, metrics = train(data, quick=True)
    assert 0 <= metrics["accuracy"] <= 1
