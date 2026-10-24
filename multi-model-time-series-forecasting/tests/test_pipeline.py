"""Tests for the forecasting and the speech recognition."""
import numpy as np
import pandas as pd

from src.data import load_data
from src.model import (
    infer_period,
    linear_trend,
    mase,
    moving_average,
    rolling_origin_evaluation,
    seasonal_naive,
    seasonal_naive_with_trend,
    train,
    demo,
)


def _series(values):
    return pd.DataFrame({"value": values})


def test_the_seasonal_forecast_keeps_the_days_in_the_week():
    # Two weeks of the same numbers.
    history = _series([1, 2, 3, 4, 5, 6, 7] * 2)
    forecast = seasonal_naive(history, 7)

    assert len(forecast) == 7
    # The forecast carries on with the season: the day after the last day is
    # the first day of the week.
    assert list(forecast) == [1, 2, 3, 4, 5, 6, 7]


def test_the_seasonal_forecast_of_a_short_history():
    history = _series([1, 2, 3])
    forecast = seasonal_naive(history, 3)
    assert len(forecast) == 3


def test_the_trend_is_added_to_the_season():
    history = _series([1, 2, 3, 4, 5, 6, 7] * 2)
    forecast = seasonal_naive_with_trend(history, 7)
    assert len(forecast) == 7
    # The trend of the last season is one, so the forecast goes up.
    assert forecast[-1] > forecast[0]


def test_the_season_is_worked_out_of_the_data():
    """The period of the week is found and not assumed."""
    values = [1, 2, 3, 4, 5, 6, 7] * 6
    assert infer_period(values) == 7

    # A series without a season has a period of one.
    assert infer_period(list(range(40))) == 1


def test_the_moving_average_is_flat():
    history = _series([1, 2, 3, 4, 5, 6, 7])
    forecast = moving_average(history, 3)
    assert list(forecast) == [4.0, 4.0, 4.0]


def test_the_linear_trend_follows_the_line():
    history = _series(list(range(10)))
    forecast = linear_trend(history, 3)
    assert forecast[0] < forecast[1] < forecast[2]


def test_the_scaled_error_is_a_number():
    history = _series(list(range(20)))
    forecast = linear_trend(history, 5)
    truth = list(range(20, 25))
    value = mase(history, forecast, truth)
    assert value >= 0
    assert value != float("inf")


def test_the_models_are_measured_on_a_few_windows():
    data = load_data(seed=1, quick=True)
    models = {
        "seasonal_naive": seasonal_naive,
        "moving_average": moving_average,
        "linear_trend": linear_trend,
    }
    results = rolling_origin_evaluation(data, models, folds=2, horizon=7)
    assert set(results) == set(models)
    for name, value in results.items():
        assert value is None or value >= 0, name


def test_the_pipeline_runs(capsys):
    data = load_data(seed=1, quick=True)
    model, metrics = train(data, quick=True)
    assert model is not None
    assert isinstance(metrics, dict) and metrics
    demo(data)
    assert capsys.readouterr().out.strip()
