# Luigi Batch ETL Orchestrator

A small task graph with outputs, dependencies and a local runner.

> Implement a multi-task batch ETL workflow (extract, transform, load) with Luigi including dependencies, retries, failure handling and a monitoring view.

## Overview

An original, self-contained implementation of the **Luigi Batch ETL Orchestrator** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Task classes for extract, clean, aggregate and load
- Dependency resolution through requires()
- Marker files for task outputs
- SQLite load with category totals

## Stack

`Python; NumPy; Pandas`
The CSV stack is Python + NumPy + Pandas. Luigi is not installed, so task classes and a recursive runner implement the dependency graph locally.

## Run

```bash
pip install -r requirements.txt
python main.py run
python main.py demo
pytest -q
```

## Structure

```text
luigi-batch-etl-orchestrator/
├── main.py                 pipeline CLI
├── src/pipeline.py         data pipeline
├── tests/test_pipeline.py  smoke test
├── requirements.txt
```

## Testing

```bash
pytest -q
```

6 tests (`pytest -q`), up from 2.

## Notes and limitations

- There is no central scheduler or visualiser.
- Files are always rewritten; task output checks are shown but not used for skipping.
- SQLite stands in for PostgreSQL.

## License

Apache-2.0. See `LICENSE`.

## About the scope

This is a third-year student project, not a production data platform. It uses local files and SQLite so the pipeline can run on one machine. The notes above list the production pieces that were replaced or skipped.
