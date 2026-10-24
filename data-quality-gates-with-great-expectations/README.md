# Data Quality Gates with Great Expectations

Data quality gates over a messy customer export.

> Add an automated data-quality layer that profiles datasets, defines expectation suites and blocks bad loads with generated data docs.

## Overview

An original, self-contained implementation of the **Data Quality Gates with Great Expectations** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Every check is written down once: it says what it looks at and how severe
  it is, and both the number of the failures and the cleaning of the table
  come from it
- The report names the rows that failed and the checks they failed, and it
  holds an example of every failure
- The critical failures and the warnings are counted apart, and only the rows
  of a critical check are thrown away

## Stack

`Python; NumPy; Pandas`
The CSV stack is Python + NumPy + Pandas. Great Expectations is not available, so the quality checks are plain pandas functions and the report is JSON.

## Run

```bash
pip install -r requirements.txt
python main.py run
python main.py demo
pytest -q
```

## Structure

```text
data-quality-gates-with-great-expectations/
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

13 tests: every check on its own, the report that names the rows, the
severities that are counted apart, the cleaned table and the agreement
between the report and the cleaning.
```

## Notes and limitations

- The checks are hand-written functions instead of an expectation suite.
- The pipeline does not run inside Airflow.
- The report is JSON; there is no data docs site.

## License

Apache-2.0. See `LICENSE`.

## About the scope

This is a third-year student project, not a production data platform. It uses local files and SQLite so the pipeline can run on one machine. The notes above list the production pieces that were replaced or skipped.
