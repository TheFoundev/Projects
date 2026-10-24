# Algorithmic Trading Signals

Technical indicators and a small next-day direction model.

> Turn market and technical data into trading strategies: feature engineering, supervised return prediction, backtesting, and portfolio-level evaluation.

## Overview

An original, self-contained implementation of the **Algorithmic Trading Signals** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- RSI, moving averages, a gap feature and a momentum feature (the rate of
  change over ten days)
- A random forest that says whether the price goes up the next day
- A backtest that trades the predictions, with the return, the Sharpe ratio
  and the drawdown
- The buy and hold of the same window as the baseline

## Stack

`Python; pandas; scikit-learn; TA-Lib`

The CSV stack is pandas + scikit-learn + TA-Lib. TA-Lib is a native dependency, so the indicators are implemented directly with pandas and NumPy.

## Run

```bash
pip install -r requirements.txt
python main.py train
python main.py demo
pytest -q
```

## Structure

```text
algorithmic-trading-signals/
├── main.py                 train / demo CLI
├── src/data.py             dataset builder
├── src/model.py            model and evaluation
├── tests/test_pipeline.py  smoke test
├── requirements.txt
```

## Testing

```bash
pytest -q
```

11 tests: the RSI, the features and the momentum feature, the last row
(which has no next day and may not carry a target of zero), the forward
return of the backtest, the buy and hold baseline and the days that were
traded.

## Notes and limitations

- Prices are simulated; results say nothing about real markets.
- The backtest ignores fees, slippage, position sizing and short selling.
- A real study needs walk-forward validation, multiple assets and proper risk controls.

## License

MIT. See `LICENSE`.

## About the scope

This is a third-year student project, not a production system. The code is small enough to read in one sitting and focuses on the core idea from the brief. The notes above list the parts that are simplified or simulated.
