"""The domain logic behind the API of the batch pipeline.

The chain of the tasks is really executed: the rows are extracted, cleaned,
aggregated and loaded, and the summary reports what the run produced.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from src.pipeline import run  # noqa: E402


def summary():
    result = run(quick=True, base_dir=str(ROOT / "artifacts"))
    summary_frame = pd.read_csv(ROOT / "artifacts" / "aggregate" / "category_summary.csv")
    return {
        "stats": {
            "tasks_executed": result["tasks_executed"],
            "raw_rows": result["raw_rows"],
            "clean_rows": result["clean_rows"],
            "revenue": result["revenue"],
        },
        "series": [
            {"label": str(row["category"]), "value": round(float(row["revenue"]), 2)}
            for _, row in summary_frame.iterrows()
        ],
        "lists": {
            "tasks": [
                {"step": index + 1, "task": task}
                for index, task in enumerate(result["task_order"].split(","))
            ],
            "categories": [
                {"category": str(row["category"]), "orders": int(row["orders"]),
                 "revenue": round(float(row["revenue"]), 2)}
                for _, row in summary_frame.iterrows()
            ],
        },
    }


def handle(method, path, payload, user):
    if method == "POST" and path.endswith("/run"):
        return 200, summary()
    return 404, {"error": "not found"}
