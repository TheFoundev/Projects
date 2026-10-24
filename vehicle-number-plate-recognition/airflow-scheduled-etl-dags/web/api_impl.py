"""The API of the project: the numbers of the last run of the pipeline.

The summary comes from the real pipeline: the tasks are run in the order of
the dependency graph, the raw orders, the clean orders and the daily revenue
are written, and the history of the runs is read back from the warehouse.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.pipeline import DEPENDENCIES, run  # noqa: E402

#: Where the pipeline writes the raw orders, the clean ones and the warehouse.
BASE_DIR = ROOT / "artifacts"
WAREHOUSE = BASE_DIR / "warehouse.db"

#: The summary of the last run, kept for the life of the process.
_STATE: dict = {}


def run_pipeline() -> dict:
    """Run the pipeline and keep the summary of the run."""
    summary = run(quick=False, base_dir=str(BASE_DIR))
    _STATE["summary"] = summary
    return summary


def history() -> list:
    """The history of the runs: the task, its state, its rows and its time."""
    if not WAREHOUSE.exists():
        return []
    connection = sqlite3.connect(WAREHOUSE)
    rows = connection.execute(
        "SELECT task, status, rows, seconds, finished_at FROM task_runs ORDER BY rowid"
    ).fetchall()
    connection.close()
    return [
        {
            "task": row[0],
            "status": row[1],
            "rows": row[2],
            "seconds": round(row[3], 3),
            "finished_at": row[4],
        }
        for row in rows
    ]


def tasks() -> list:
    """The tasks of the DAG with the task each of them needs.

    The state and the rows of a task come from the last run, so the table
    shows what the run really did.
    """
    summary = _STATE.get("summary") or run_pipeline()
    order = summary["order"]
    last = history()[-len(order):] if len(history()) >= len(order) else []
    states = {row["task"]: row for row in last}
    return [
        {
            "task": name,
            "needs": ", ".join(DEPENDENCIES.get(name, [])) or "-",
            "status": states.get(name, {}).get("status", "-"),
            "rows": states.get(name, {}).get("rows", 0),
        }
        for name in order
    ]


def summary() -> dict:
    """The state of the last run: the tasks, the rows and the days."""
    summary = _STATE.get("summary") or run_pipeline()
    task_rows = tasks()
    return {
        "stats": {
            "tasks": summary["tasks"],
            "raw_rows": summary["raw_rows"],
            "clean_rows": summary["clean_rows"],
            "daily_rows": summary["daily_rows"],
        },
        "series": [
            {"label": row["task"], "value": row["rows"]} for row in task_rows
        ],
        "lists": {
            "tasks": task_rows,
            "history": history()[-20:][::-1],
        },
    }


def handle(method, path, payload, user):
    """The read and the write endpoints of the project."""
    if method == "GET" and path == "/api/tasks":
        return 200, {"tasks": tasks()}
    if method == "GET" and path == "/api/history":
        return 200, {"history": history()[-20:][::-1]}
    if method == "POST" and path == "/api/run":
        run_pipeline()
        return 200, summary()["stats"]
    return 404, {"error": "not found"}
