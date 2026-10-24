# Multi-Model Time-Series Forecasting

Compare simple forecasting baselines on a seasonal series.

> Benchmark classical and deep forecasters (ARIMA, TCN, N-BEATS, Transformer) on multivariate energy or traffic series with proper rolling-window backtesting.

## Overview

An original, self-contained implementation of the **Multi-Model Time-Series Forecasting** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Synthetic series with trend and weekly seasonality
- Naive, mean, linear-trend and seasonal-naive baselines
- Optional SARIMAX comparison
- MAE/RMSE table and a forecast plot

## Stack

`Python; Matplotlib; NumPy; Pandas`
The CSV stack is Python + Matplotlib + NumPy + Pandas. Darts is not installed, so the models are implemented with NumPy and pandas; statsmodels provides SARIMAX.

## Run

```bash
pip install -r requirements.txt
python main.py train
python main.py demo
pytest -q
```

## Structure

```text
multi-model-time-series-forecasting/
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

9 tests (`pytest -q`), up from 2: the season, the forecasts, the scaled error and the evaluation over a few windows.


## Notes and limitations

- The series is simulated and much cleaner than real sales or traffic data.
- No neural forecasting model is trained.
- Only one holdout split is used, not rolling-origin evaluation.

## License

Apache-2.0. See `LICENSE`.

## About the scope

This is a third-year student project, not a production system. The code is small enough to read in one sitting and focuses on the core idea from the brief. The notes above list the parts that are simplified or simulated.
