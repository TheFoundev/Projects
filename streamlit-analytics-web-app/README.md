# Streamlit Analytics Web App

A filterable subscription analytics app without Streamlit.

> Ship a self-service analytics web app with file uploads, filters, charts and shareable reports written entirely in Python.

## Overview

An original, self-contained implementation of the **Streamlit Analytics Web App** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- A Streamlit page with filters for the segment, the region and the months
- The MRR, the ARR, the active customers, the average fee, the churn and the
  net revenue retention, with the definitions written down
- The revenue of every month, with the new and the churned customers
- A cohort table: how much of every cohort is still there
- A chart of the revenue by segment
- The table of the customers and a download of it

## Stack

`Python; Streamlit; Pandas; Plotly`

The CSV stack is Streamlit + Pandas, and that is what the project uses: the
page is a Streamlit app, the data comes from a file that is read once and
cached, and the numbers are worked out in `src/pipeline.py` where they can be
tested.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
python main.py demo
pytest -q
```



## Structure

```text
streamlit-analytics-web-app/
├── main.py                 pipeline CLI
├── src/pipeline.py         data pipeline
├── tests/test_pipeline.py  smoke test
├── requirements.txt
├── app.py                  the Streamlit page
```

## Testing

```bash
pytest -q
```

15 tests: a subscription is active from its start month and stops at its
churn month, the MRR, the ARR, the average fee, the churn and the net
revenue retention, the MRR of every month, the cohort table, the filters and
the data being saved and read back.

## Notes and limitations

- The app is not reactive like Streamlit; filters submit a form.
- Data is generated once per run and stored as CSV.
- There are no charts or user accounts.

## License

Apache-2.0. See `LICENSE`.

## About the scope

This is a third-year student project, not a production data platform. It uses local files and SQLite so the pipeline can run on one machine. The notes above list the production pieces that were replaced or skipped.
