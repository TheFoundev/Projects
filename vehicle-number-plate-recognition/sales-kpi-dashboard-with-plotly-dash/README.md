# Sales KPI Dashboard with Plotly Dash

A small sales KPI dashboard backed by a local warehouse.

> Build an interactive business-intelligence dashboard with callbacks, drill-downs and KPI cards on top of a relational sales dataset.

## Overview

An original, self-contained implementation of the **Sales KPI Dashboard with Plotly Dash** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Ninety days of synthetic sales orders
- Revenue, orders, average order value and growth KPIs
- Top product and region summaries
- Trend chart and a Flask dashboard

## Stack

`Python; Flask; Matplotlib; NumPy; Pandas`
The CSV stack is Python + Flask + Matplotlib + NumPy + Pandas. Dash and PostgreSQL are not installed, so this build computes KPIs with pandas and serves them through Flask.

## Run

```bash
pip install -r requirements.txt
python main.py run
python app.py
python main.py demo
pytest -q
```

## Structure

```text
sales-kpi-dashboard-with-plotly-dash/
├── main.py                 pipeline CLI
├── src/pipeline.py         data pipeline
├── tests/test_pipeline.py  smoke test
├── requirements.txt
├── app.py                  Flask KPI dashboard
```

## Testing

```bash
pytest -q
```

3 tests (`pytest -q`), up from 2.


## Notes and limitations

- The data is generated locally, not connected to a business system.
- Growth compares the last thirty days with the previous thirty.
- The dashboard is a single page without user accounts or filters.

## License

MIT. See `LICENSE`.

## About the scope

This is a third-year student project, not a production data platform. It uses local files and SQLite so the pipeline can run on one machine. The notes above list the production pieces that were replaced or skipped.
