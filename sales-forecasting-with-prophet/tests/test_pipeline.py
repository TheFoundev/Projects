"""Tests for the sales forecast."""
from src.data import load_data
from src.model import demo, fit, predict, train, weekend_effect_lookup


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


def test_the_model_is_fitted_on_the_training_data():
    data = load_data(seed=3, quick=True)
    model = fit(data)
    assert "intercept" in model
    assert "slope" in model
    assert "weekday_effect" in model


def test_the_weekday_effect_is_looked_up():
    data = load_data(seed=3, quick=True)
    model = fit(data)
    import numpy as np

    days = np.array([0, 1, 2, 3, 4, 5, 6])
    effect = weekend_effect_lookup(days, model["weekday_effect"])
    assert len(effect) == 7


def test_the_prediction_follows_the_trend():
    data = load_data(seed=3, quick=True)
    model = fit(data)
    import numpy as np

    early = predict(model, np.array([1]))
    late = predict(model, np.array([100]))
    assert late[0] > early[0]


def test_the_error_is_a_number():
    data = load_data(seed=4, quick=True)
    _, metrics = train(data, quick=True)
    assert metrics["mae"] >= 0
