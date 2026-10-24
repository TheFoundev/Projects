"""Tests for the hybrid recommender and its metrics."""
import numpy as np

from src.data import load_data
from src.model import fit, recommend, precision_at_k, train, demo


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


def test_the_recommendations_never_include_a_seen_item():
    data = load_data(seed=2, quick=True)
    model = fit(data)
    for user in range(min(5, data["n_users"])):
        items = [item for item, _ in recommend(model, data, user, 5)]
        seen = set(np.where(model["seen"][user])[0].tolist())
        assert not (set(items) & seen)


def test_the_precision_is_a_share():
    """The precision may not be bigger than one.

    The old metric divided the hits by the number of users times five, so it
    could never be bigger than one fifth.
    """
    data = load_data(seed=4, quick=True)
    model = fit(data)
    value = precision_at_k(model, data, 5)
    assert 0 <= value <= 1


def test_more_recommendations_find_at_least_as_many_hits():
    """More recommendations find at least as many of the relevant items."""
    data = load_data(seed=4, quick=True)
    model = fit(data)

    def hits(k):
        found = 0
        relevant = data["test"][data["test"]["rating"] >= 4]
        for user, group in relevant.groupby("user_id"):
            if int(user) >= data["n_users"]:
                continue
            items = {item for item, _ in recommend(model, data, int(user), k)}
            found += len(items & set(group["item_id"].astype(int)))
        return found

    assert hits(20) >= hits(5)
