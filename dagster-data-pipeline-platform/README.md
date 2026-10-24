# Dagster Data Pipeline Platform

An asset-oriented customer pipeline with lineage logging.

> Build a software-defined data platform with Dagster assets, schedules, sensors and lineage for a multi-source analytics pipeline.

## Overview

An original, self-contained implementation of the **Dagster Data Pipeline Platform** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- The assets depend on each other, and the materialisation log says which
  asset depends on which and which run it belongs to
- The customers are grouped with the RFM model: how recently they signed up,
  how often they order and what they are worth, scored by their fifth
- The assets are written as Parquet files

## Stack

`Python; NumPy; Pandas`
The CSV stack is Python + NumPy + Pandas. Dagster is not installed, so the asset graph is executed by a small local runner and lineage is stored in SQLite.

## Run

```bash
pip install -r requirements.txt
python main.py run
python main.py demo
pytest -q
```

## Structure

```text
dagster-data-pipeline-platform/
├── main.py                 pipeline CLI
├── src/pipeline.py         data pipeline
├── tests/test_pipeline.py  smoke test
├── requirements.txt
```

## Testing

```bash
```bash
pytest -q
```

8 tests: the graph of the assets, that the duplicates are removed, that the
log holds the dependencies and one run id per run, the RFM groups and the
report of the groups.
```

## Notes and limitations

- The asset graph is executed by a plain function, not a Dagster daemon.
- SQLite stores lineage metadata; the warehouse tables are local Parquet files.
- There is no scheduling, partitioning or backfill UI.

## License

Apache-2.0. See `LICENSE`.

## About the scope

This is a third-year student project, not a production data platform. It uses local files and SQLite so the pipeline can run on one machine. The notes above list the production pieces that were replaced or skipped.
