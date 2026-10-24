"""The API of the subscription analytics.

The numbers are the real ones: the subscriptions are the ones the project
made (or the ones it saved in artifacts/subscriptions.csv) and every number
comes from the functions of src/pipeline.py, the same ones the Streamlit page
of the project uses. The page and this API cannot disagree, because they read
the same table and the same metrics.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.pipeline import (  # noqa: E402
    CURRENT_MONTH,
    MONTHS,
    cohort_retention,
    load,
    mrr_by_month,
)
from src.pipeline import summary as pipeline_summary  # noqa: E402

#: The subscriptions of the project, read once and kept.
_CACHE: dict[str, object] = {}


def _frame():
    """The subscriptions of the project."""
    if "frame" not in _CACHE:
        _CACHE["frame"] = load(base_dir=str(ROOT / "artifacts"))
    return _CACHE["frame"]


def _numbers():
    """The metrics of the current month."""
    return pipeline_summary(_frame(), CURRENT_MONTH)


def _monthly() -> list[dict]:
    """The MRR, the customers, the new and the churned of every month."""
    monthly = mrr_by_month(_frame(), MONTHS)
    return [
        {
            "month": str(row["month"]),
            "mrr": float(row["mrr"]),
            "customers": int(row["customers"]),
            "new": int(row["new"]),
            "churned": int(row["churned"]),
        }
        for _, row in monthly.iterrows()
    ]


def _segments() -> list[dict]:
    """The MRR and the customers of every segment."""
    numbers = _numbers()
    return [
        {
            "segment": str(row["segment"]),
            "customers": int(row["customers"]),
            "mrr": float(row["mrr"]),
        }
        for row in numbers["by_segment"]
    ]


def _cohorts() -> list[dict]:
    """How much of every cohort is still there in every month."""
    cohorts = cohort_retention(_frame(), MONTHS)
    rows = []
    for _, row in cohorts.iterrows():
        entry = {"cohort": str(row["cohort"]), "customers": int(row["customers"])}
        for month in MONTHS:
            value = row.get(month)
            entry[month] = None if value is None or value != value else float(value)
        rows.append(entry)
    return rows


def summary():
    numbers = _numbers()
    monthly = _monthly()

    return {
        "stats": {
            "mrr": numbers["mrr"],
            "arr": numbers["arr"],
            "active": numbers["active"],
            "churn_rate": round(numbers["churn_rate"] * 100, 2),
        },
        "series": [
            {"label": row["month"], "value": row["mrr"]}
            for row in monthly
        ],
        "lists": {
            "monthly": monthly,
            "segments": _segments(),
            "cohorts": _cohorts(),
        },
    }


def handle(method, path, payload, user):
    if method == "GET" and path == "/api/monthly":
        return 200, {"monthly": _monthly()}

    if method == "GET" and path == "/api/segments":
        return 200, {"segments": _segments()}

    if method == "GET" and path == "/api/cohorts":
        return 200, {"cohorts": _cohorts()}

    return 404, {"error": "not found"}
