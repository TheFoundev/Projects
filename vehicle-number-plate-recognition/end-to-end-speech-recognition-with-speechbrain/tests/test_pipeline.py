"""Tests for the speech recognition."""
import numpy as np

from src.data import features, load_data
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


def test_the_data_is_split_in_two():
    data = load_data(seed=2, quick=True)
    assert len(data["X_train"]) > 0
    assert len(data["X_test"]) > 0
    assert len(data["y_train"]) == len(data["X_train"])


def test_the_features_have_the_size_that_was_asked_for():
    data = load_data(seed=2, quick=True)
    vector = features(data["X_train"][0], frames=20, bands=12)
    assert vector.shape == (240,)
    assert np.isfinite(vector).all()


def test_the_features_of_two_signals_are_not_the_same():
    data = load_data(seed=2, quick=True)
    first = features(data["X_train"][0])
    second = features(data["X_train"][1])
    assert not np.array_equal(first, second)


def test_the_accuracy_is_a_share():
    data = load_data(seed=4, quick=True)
    _, metrics = train(data, quick=True)
    assert 0 <= metrics["accuracy"] <= 1
