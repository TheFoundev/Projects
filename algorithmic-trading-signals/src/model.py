"""Indicator features, a direction classifier and a small backtest."""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

#: The features the model reads.
FEATURES = ["return_1d", "sma_5", "sma_20", "rsi_14", "gap", "roc_10"]


def rsi(series, period=14):
    """The relative strength index of a price series."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    return 100 - 100 / (1 + rs)


def add_features(frame):
    """The features and the target of every day.

    The target says whether the price goes up the next day. The last row has
    no next day, so it is dropped instead of being given a target of zero.
    """
    out = frame.copy()
    out["return_1d"] = out["close"].pct_change()
    out["sma_5"] = out["close"].rolling(5).mean()
    out["sma_20"] = out["close"].rolling(20).mean()
    out["rsi_14"] = rsi(out["close"])
    out["gap"] = out["close"] / out["sma_20"] - 1
    out["roc_10"] = out["close"].pct_change(10)
    # The direction of the next day. The row without a next day is dropped
    # below, because a target of zero would be a lie.
    out["target"] = (out["close"].shift(-1) > out["close"]).astype(float)
    out.loc[out["close"].shift(-1).isna(), "target"] = np.nan
    # The rows without the features they need and the last row, which has no
    # next day, are dropped.
    return out.dropna(subset=FEATURES + ["target"]).reset_index(drop=True)



def forward_returns(frame):
    """The return of every day to the next one.

    The return of day i is (close[i+1] - close[i]) / close[i], which is the
    return the prediction of day i is about.
    """
    close = frame["close"].to_numpy(dtype=float)
    if len(close) < 2:
        return np.zeros(0)
    return close[1:] / close[:-1] - 1


def train(data, quick=False):
    """Fit the classifier and run the backtest."""
    train_frame = add_features(data["train"])
    test_frame = add_features(data["test"])

    model = RandomForestClassifier(
        n_estimators=40 if quick else 140,
        max_depth=4,
        min_samples_leaf=5,
        random_state=7,
    )
    model.fit(train_frame[FEATURES], train_frame["target"])
    predictions = model.predict(test_frame[FEATURES])
    accuracy = accuracy_score(test_frame["target"], predictions)

    # The return that every prediction is about.
    returns = forward_returns(test_frame)
    # The last day of the test set has no next day, so it cannot be traded.
    traded = predictions[:-1] if len(predictions) > len(returns) else predictions
    traded_returns = returns[:len(traded)]

    strategy_returns = traded_returns * (traded == 1)
    strategy_total = float(np.prod(1 + strategy_returns) - 1)

    # The baseline is the price of the whole window, not a series of returns.
    close = test_frame["close"].to_numpy(dtype=float)
    buy_hold_total = float(close[-1] / close[0] - 1)

    volatility = float(np.std(strategy_returns) + 1e-9)
    sharpe = float(np.mean(strategy_returns) / volatility * np.sqrt(252))
    curve = np.cumprod(1 + strategy_returns)
    drawdown = float(np.min(curve / np.maximum.accumulate(curve) - 1))

    metrics = {
        "accuracy": round(float(accuracy), 4),
        "strategy_return": round(strategy_total, 4),
        "buy_hold_return": round(buy_hold_total, 4),
        "sharpe_like": round(sharpe, 3),
        "max_drawdown": round(drawdown, 4),
        "test_days": int(len(test_frame)),
        "traded_days": int(len(traded_returns)),
    }
    return model, metrics


def demo(data):
    model, metrics = train(data, quick=True)
    frame = add_features(data["prices"])
    latest = frame.iloc[-1]
    probability = model.predict_proba(frame[FEATURES].tail(1))[0]
    direction = "up" if probability[1] >= 0.5 else "down"
    print(f"Latest close: {latest['close']:.2f}")
    print(f"RSI(14): {latest['rsi_14']:.1f}")
    print(f"Model view for tomorrow: {direction} (p={probability[1]:.2f})")
    print(f"Quick backtest accuracy: {metrics['accuracy']:.3f}")
    print(f"Strategy: {metrics['strategy_return'] * 100:.1f}%, buy and hold: {metrics['buy_hold_return'] * 100:.1f}%")
