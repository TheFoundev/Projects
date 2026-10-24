# ML Experiment Tracking and Registry

A tiny experiment tracker and model registry backed by SQLite.

> Operationalize an ML project lifecycle: track experiments, version datasets and models in a registry, and deploy a reproducible REST prediction endpoint.

## Overview

An original, self-contained implementation of the **ML Experiment Tracking and Registry** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Train three model configurations on the same split
- Log parameters, metrics and artefact paths to SQLite
- Best-run lookup and a simple model registry
- FastAPI endpoints for runs and the current best model

## Stack

`Python; NumPy; scikit-learn`
The CSV stack is Python + NumPy + scikit-learn. MLflow is too heavy for this portfolio build, so the same ideas are reduced to a SQLite run table and a CLI.

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
ml-experiment-tracking-and-registry/
├── main.py                 train / demo CLI
├── src/data.py             dataset builder
├── src/model.py            model and evaluation
├── tests/test_pipeline.py  smoke test
├── requirements.txt
├── app.py                  FastAPI registry API
```

## Testing

```bash
pytest -q
```

6 tests (`pytest -q`), up from 2.


## Notes and limitations

- Artefacts are pickled locally; there is no remote store or model server.
- Runs are not nested and there is no UI beyond the JSON API.
- The registry is a table lookup, not a governed production registry.

## License

Apache-2.0. See `LICENSE`.

## About the scope

This is a third-year student project, not a production system. The code is small enough to read in one sitting and focuses on the core idea from the brief. The notes above list the parts that are simplified or simulated.
