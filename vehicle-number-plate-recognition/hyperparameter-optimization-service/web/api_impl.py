"""The domain logic behind the API of the hyper-parameter search.

The numbers come from the real search: the trials of the SQLite database of
the project are read, and the best trial is recomputed when the database is
empty.
"""
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.data import load_data  # noqa: E402
from src.model import run_search  # noqa: E402

DB_PATH = ROOT / "artifacts" / "trials.db"


def _trials():
    if not DB_PATH.exists():
        return []
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    rows = connection.execute(
        "SELECT id, params, accuracy, f1 FROM trials ORDER BY accuracy DESC"
    ).fetchall()
    connection.close()
    return [dict(row) for row in rows]


def summary():
    rows = _trials()
    if not rows:
        # Nothing has been searched yet: run a short real search so the
        # console shows the state of the project and not a blank page.
        data = load_data(seed=42, quick=True)
        run_search(data, trials=4, seed=7, db_path=str(DB_PATH))
        rows = _trials()
    best = rows[0] if rows else {}
    return {
        "stats": {
            "trials": len(rows),
            "best_accuracy": round(best.get("accuracy") or 0.0, 4),
            "best_f1": round(best.get("f1") or 0.0, 4),
            "features": 12,
        },
        "series": [
            {"label": f"trial {row['id']}", "value": round(row["accuracy"], 4)} for row in rows[-12:]
        ],
        "lists": {
            "trials": [
                {
                    "id": row["id"],
                    "params": json.dumps(json.loads(row["params"]), separators=(",", ":")),
                    "accuracy": round(row["accuracy"], 4),
                    "f1": round(row["f1"], 4),
                }
                for row in rows
            ]
        },
    }


def handle(method, path, payload, user):
    if method == "GET" and path.endswith("/trials"):
        return 200, {"trials": _trials()}
    if method == "POST" and path.endswith("/search"):
        data = load_data(seed=42, quick=True)
        run_search(data, trials=int(payload.get("trials", 8)), seed=int(payload.get("seed", 7)),
                   db_path=str(DB_PATH))
        return 200, summary()
    return 404, {"error": "not found"}
