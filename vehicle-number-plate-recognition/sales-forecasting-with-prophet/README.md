# Sales Forecasting with Prophet

A Prophet-style additive sales forecast with weekly and yearly effects.

> Forecast retail sales, demand, or web traffic with Prophet seasonality and holiday components, producing prediction intervals for business planning dashboards.

## Overview

An original, self-contained implementation of the **Sales Forecasting with Prophet** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Synthetic daily sales with trend, weekly and yearly patterns
- Additive decomposition and a horizon forecast
- Holiday bumps included in the generator
- MAE, MAPE and forecast plot

## Stack

`Python; Matplotlib; NumPy; Pandas`
The CSV stack is Python + Matplotlib + NumPy + Pandas. Prophet is not installed, so the project fits the same additive structure with NumPy least squares.

## Run

```bash
pip install -r requirements.txt
python main.py train
python main.py demo
pytest -q
```

## Structure

```text
sales-forecasting-with-prophet/
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

6 tests (`pytest -q`), up from 2.


## Notes and limitations

- The sales series is synthetic; no store data is used.
- The forecast does not model promotions or inventory constraints.
- Confidence intervals and changepoint detection are not implemented.

## License

MIT. See `LICENSE`.

## About the scope

This is a third-year student project, not a production system. The code is small enough to read in one sitting and focuses on the core idea from the brief. The notes above list the parts that are simplified or simulated.
