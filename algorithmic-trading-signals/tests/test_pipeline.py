"""Tests for the indicators, the classifier and the backtest."""
import numpy as np
import pandas as pd

from src.data import load_data
from src.model import FEATURES, add_features, forward_returns, rsi, train, demo


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


# ---------------------------------------------------------------------------
# The features
# ---------------------------------------------------------------------------

def test_the_rsi_of_a_rising_series_is_high():
    series = pd.Series(np.arange(1, 40, dtype=float))
    value = rsi(series).iloc[-1]
    assert value > 90


def test_the_rsi_of_a_falling_series_is_low():
    series = pd.Series(np.arange(40, 1, -1, dtype=float))
    value = rsi(series).iloc[-1]
    assert value < 10


def test_the_last_row_has_no_target():
    """The last day has no next day, so it may not carry a target of zero."""
    data = load_data(seed=2, quick=True)
    frame = add_features(data["prices"])

    assert len(frame) < len(data["prices"])
    assert frame["target"].notna().all()
    assert set(frame["target"].unique()) <= {0.0, 1.0}


def test_the_features_are_the_ones_the_model_reads():
    data = load_data(seed=2, quick=True)
    frame = add_features(data["prices"])
    for feature in FEATURES:
        assert feature in frame.columns
        assert frame[feature].notna().all()
    assert frame["roc_10"].notna().all()


def test_the_momentum_feature_is_there():
    """The README promises a momentum feature, so there has to be one."""
    assert "roc_10" in FEATURES


# ---------------------------------------------------------------------------
# The backtest
# ---------------------------------------------------------------------------

def test_the_forward_return_is_the_return_to_the_next_day():
    frame = pd.DataFrame({"close": [100.0, 110.0, 99.0]})
    returns = forward_returns(frame)

    assert len(returns) == 2
    assert abs(returns[0] - 0.1) < 1e-9
    assert abs(returns[1] - (-0.1)) < 1e-9


def test_the_buy_and_hold_is_the_price_of_the_window():
    data = load_data(seed=5, quick=True)
    _, metrics = train(data, quick=True)

    frame = add_features(data["test"])
    expected = frame["close"].iloc[-1] / frame["close"].iloc[0] - 1
    assert abs(metrics["buy_hold_return"] - expected) < 0.001


def test_the_backtest_reports_the_days_it_traded():
    data = load_data(seed=5, quick=True)
    _, metrics = train(data, quick=True)

    assert metrics["traded_days"] <= metrics["test_days"]
    assert metrics["traded_days"] > 0


def test_the_accuracy_is_a_share():
    data = load_data(seed=5, quick=True)
    _, metrics = train(data, quick=True)
    assert 0 <= metrics["accuracy"] <= 1
