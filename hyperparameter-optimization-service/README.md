# Hyperparameter Optimization Service

A small random-search service that records every trial.

> Systematically optimize model hyperparameters and pruning schedules with Optuna's TPE sampler and visualizations, embedded into a reproducible training workflow.

## Overview

An original, self-contained implementation of the **Hyperparameter Optimization Service** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Synthetic classification dataset
- Random search over random-forest hyperparameters
- SQLite trial log with parameters and scores
- FastAPI endpoints for search and results

## Stack

`Python; NumPy; scikit-learn`
The CSV stack is Python + NumPy + scikit-learn. Optuna is replaced with a small random-search loop; scikit-learn and FastAPI are used directly.

## Run

```bash
pip install -r requirements.txt
python main.py train
python app.py
python main.py demo
pytest -q
```

## Structure

```text
hyperparameter-optimization-service/
├── main.py                 train / demo CLI
├── src/data.py             dataset builder
├── src/model.py            model and evaluation
├── tests/test_pipeline.py  smoke test
├── requirements.txt
├── app.py                  FastAPI service
```

## Testing

```bash
pytest -q
```

6 tests (`pytest -q`), up from 2.
Added `pydantic` to the requirements: `app.py` imports it and the documented run command failed without it.


## Notes and limitations

- The search space is deliberately tiny and runs on one CPU.
- There is no pruning, distributed workers or persistent study server.
- SQLite is used as a simple local trial store.

## License

MIT. See `LICENSE`.

## About the scope

This is a third-year student project, not a production system. The code is small enough to read in one sitting and focuses on the core idea from the brief. The notes above list the parts that are simplified or simulated.
