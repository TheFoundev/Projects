"""Tests for the matrix factorisation and the metrics."""
import numpy as np

from src.data import load_data
from src.model import fit, predict, recommend, precision_at_5, rmse, train, demo


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


def test_the_prediction_stays_inside_the_range_of_the_ratings():
    data = load_data(seed=2, quick=True)
    model = fit(data, epochs=4)
    low, high = model["rating_range"]
    for user in range(min(5, data["n_users"])):
        for item in range(min(5, data["n_items"])):
            value = predict(model, user, item)
            assert low <= value <= high


def test_the_recommendations_never_include_a_seen_item():
    data = load_data(seed=2, quick=True)
    model = fit(data, epochs=4)
    for user in range(min(5, data["n_users"])):
        items = [item for item, _ in recommend(model, data, user, 5)]
        assert not (set(items) & model["seen"].get(user, set()))


def test_the_precision_is_a_share():
    """The precision may not be bigger than one.

    The old metric divided the hits by the number of users times five, so it
    could never be bigger than one fifth.
    """
    data = load_data(seed=4, quick=True)
    model = fit(data, epochs=6)
    value = precision_at_5(model, data)
    assert 0 <= value <= 1


def test_the_rmse_is_a_number():
    data = load_data(seed=4, quick=True)
    model = fit(data, epochs=6)
    value = rmse(model, data)
    assert value >= 0
