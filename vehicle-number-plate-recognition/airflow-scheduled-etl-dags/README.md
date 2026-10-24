# Airflow Scheduled ETL DAGs

A dependency-ordered orders ETL job with a tiny Airflow-style DAG.

> Design, deploy and monitor scheduled ETL DAGs with Apache Airflow including backfills, sensors, SLAs and alerting.

## Overview

An original, self-contained implementation of the **Airflow Scheduled ETL DAGs** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- A real Airflow DAG in `dags/orders_dag.py`, with the tasks, their
  dependencies, the retries and the schedule
- The local runner does the same work, so the pipeline runs without Airflow
- The order of the tasks comes from the dependency graph, not from the order
  they are written in
- A task that fails is retried, and the tasks that already ran are marked
  as rolled back
- The history of every run in the warehouse: the task, the state, the rows,
  the time and when it finished

## Stack

`Python; Airflow; Docker; PostgreSQL`

The CSV stack is Airflow + Docker + PostgreSQL. This build replaces the scheduler and database with a local runner and SQLite while keeping the same four-stage order pipeline.

## Run

```bash
pip install -r requirements.txt
python main.py run
python main.py demo
pytest -q
```

## Structure

```text
airflow-scheduled-etl-dags/
├── main.py                 pipeline CLI
├── src/pipeline.py         data pipeline
├── tests/test_pipeline.py  smoke test
├── requirements.txt
├── dags/orders_dag.py       DAG metadata
```

## Testing

```bash
pytest -q
```

13 tests: the order of the tasks (from the graph, and the errors for a
missing task and a cycle), the files the pipeline writes, the revenue of the
day, the tables of the warehouse, the history, and the failure path (the
retries, the rollback and a task that works the second time).

## Notes and limitations

- There is no scheduler daemon, worker pool or Airflow UI.
- SQLite stands in for PostgreSQL and the raw file lands on local disk.
- Failures stop the run; retries and backfills are not implemented.

## License

Apache-2.0. See `LICENSE`.

## About the scope

This is a third-year student project, not a production data platform. It uses local files and SQLite so the pipeline can run on one machine. The notes above list the production pieces that were replaced or skipped.
