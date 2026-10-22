# Out-of-Core Dataframes with Dask

Process a large CSV in chunks without holding it all in memory.

> Analyse a multi-gigabyte public dataset out of core with Dask dataframes, parallel group-bys and a results dashboard.

## Overview

An original, self-contained implementation of the **Out-of-Core Dataframes with Dask** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Partitioned synthetic order files
- Chunked pandas reads with partial aggregation
- Merged summary written to Parquet
- Memory-friendly top-product report

## Stack

`Python; NumPy; Pandas`
The CSV stack is Python + NumPy + Pandas. Dask is not installed, so this build uses chunked pandas reads and writes the aggregate to Parquet.

## Run

```bash
pip install -r requirements.txt
python main.py run
python main.py demo
pytest -q
```

## Structure

```text
out-of-core-dataframes-with-dask/
├── main.py                 pipeline CLI
├── src/pipeline.py         data pipeline
├── tests/test_pipeline.py  smoke test
├── requirements.txt
```

## Testing

```bash
pytest -q
```

4 tests (`pytest -q`), up from 2.


## Notes and limitations

- The chunked loop is a small subset of Dask's scheduler and expression graph.
- Data is synthetic and fits comfortably on a laptop.
- There is no dashboard; the summary is written to disk.

## License

BSD-3-Clause. See `LICENSE`.

## About the scope

This is a third-year student project, not a production data platform. It uses local files and SQLite so the pipeline can run on one machine. The notes above list the production pieces that were replaced or skipped.
