"""Tests for the recommenders and the metrics."""
import numpy as np

from src.data import load_data
from src.model import build_matrix, evaluate, fit_all, normalize, recommend_matrix, train, demo


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


def test_the_matrix_holds_the_ratings():
    data = load_data(seed=2, quick=True)
    matrix = build_matrix(data)
    assert matrix.shape == (data["n_users"], data["n_items"])
    assert (matrix >= 0).all()


def test_the_normalisation_keeps_the_direction():
    matrix = np.array([[3.0, 4.0]])
    normalized = normalize(matrix)
    assert abs(np.linalg.norm(normalized[0]) - 1.0) < 1e-6


def test_the_recommendations_never_include_a_seen_item():
    data = load_data(seed=2, quick=True)
    model = fit_all(data)
    for name, scores in model["scores"].items():
        for user in range(min(5, data["n_users"])):
            items = recommend_matrix(scores, model["seen"], user, 5)
            seen = set(np.where(model["seen"][user])[0].tolist())
            assert not (set(items) & seen), name


def test_the_precision_is_a_share():
    """The precision may not be bigger than one and the denominator is the
    number of recommendations that were made."""
    data = load_data(seed=4, quick=True)
    model = fit_all(data)
    results = evaluate(model, data)

    for name, values in results.items():
        assert 0 <= values["precision"] <= 1, name
        assert 0 <= values["recall"] <= 1, name
        assert 0 <= values["coverage"] <= 1, name


def test_the_recall_divides_by_the_relevant_items():
    data = load_data(seed=4, quick=True)
    model = fit_all(data)
    results = evaluate(model, data)
    relevant = data["test"][data["test"]["rating"] >= 4]

    for name, values in results.items():
        found = 0
        for user, group in relevant.groupby("user_id"):
            user = int(user)
            if user >= data["n_users"]:
                continue
            items = recommend_matrix(model["scores"][name], model["seen"], user, 5)
            found += len(set(items) & set(group["item_id"].astype(int)))
        assert abs(values["recall"] - found / max(1, len(relevant))) < 1e-9, name


def test_every_recommender_is_measured():
    data = load_data(seed=4, quick=True)
    model = fit_all(data)
    results = evaluate(model, data)
    assert set(results) == {"popularity", "item_item", "svd", "nmf"}
