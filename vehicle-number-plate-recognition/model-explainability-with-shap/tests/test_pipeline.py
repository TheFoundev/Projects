"""Tests for the explainability pipeline."""
import numpy as np
from src.data import load_data
from src.model import (
    NOISE_FEATURES,
    SIGNAL_FEATURES,
    check_against_the_truth,
    explain,
    global_importance,
    local_explanation,
    train,
    demo,
)


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


def test_the_shap_values_add_up_to_the_prediction():
    """The contributions of a prediction add up to the difference between the
    baseline of the model and the prediction itself."""
    data = load_data(seed=5, quick=True)
    model, _ = train(data, quick=True)
    explainer, values = explain(model, data, rows=25)

    prediction = model.predict(data["X_test"][:25])
    total = values.sum(axis=1)
    expected = prediction - explainer.expected_value

    assert np.allclose(total, expected, atol=1e-6)


def test_the_importance_ranks_the_features():
    data = load_data(seed=7, quick=True)
    model, _ = train(data, quick=True)
    _, values = explain(model, data, rows=40)

    importance = global_importance(values, data["features"])
    assert len(importance) == len(data["features"])
    assert all(entry["importance"] >= 0 for entry in importance)
    scores = [entry["importance"] for entry in importance]
    assert scores == sorted(scores, reverse=True)


def test_the_explanation_finds_the_signal():
    """The features that carry the signal have to be above the noise."""
    data = load_data(seed=11, quick=True)
    model, _ = train(data, quick=True)
    _, values = explain(model, data, rows=200)

    truth = check_against_the_truth(values, data["features"], data)
    assert truth["recovers_signal"], truth["ranking"]
    for name in NOISE_FEATURES:
        assert name not in truth["ranking"][: len(SIGNAL_FEATURES)]


def test_a_local_explanation_adds_up():
    data = load_data(seed=13, quick=True)
    model, _ = train(data, quick=True)
    explainer, values = explain(model, data, rows=10)

    prediction = model.predict(data["X_test"][:1])[0]
    local = local_explanation(values, data["features"], 0, prediction, explainer.expected_value)

    assert len(local["contributions"]) == len(data["features"])
    total = sum(entry["value"] for entry in local["contributions"])
    assert abs(total - (local["prediction"] - local["baseline"])) < 0.01
