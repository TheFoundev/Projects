"""The domain logic behind the API of the experiment registry.

The candidates are really trained and the runs are really written to the
SQLite registry of the project; the best run is read back from it.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.data import load_data  # noqa: E402
from src.model import best_run, candidates, train  # noqa: E402

DB_PATH = ROOT / "artifacts" / "registry.db"


def _runs():
    """The runs of the registry, read from its own database."""
    import sqlite3

    if not DB_PATH.exists():
        return []
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    rows = connection.execute(
        "SELECT name, params, accuracy, f1, artefact FROM runs ORDER BY accuracy DESC"
    ).fetchall()
    connection.close()
    return [dict(row) for row in rows]


def summary():
    rows = _runs()
    if not rows:
        # Nothing has been run yet: train the candidates for real so the
        # console shows the state of the project.
        data = load_data(seed=42, quick=True)
        train(data, quick=True)
        rows = _runs()
    best = rows[0] if rows else {}
    names = list(candidates(quick=True).keys())
    return {
        "stats": {
            "candidates": len(names),
            "runs": len(rows),
            "best_accuracy": round(float(best.get("accuracy") or 0.0), 4),
            "best_f1": round(float(best.get("f1") or 0.0), 4),
        },
        "series": [{"label": str(row["name"]), "value": round(float(row["accuracy"]), 4)} for row in rows],
        "lists": {
            "runs": [
                {"name": str(row["name"]), "accuracy": round(float(row["accuracy"]), 4),
                 "f1": round(float(row["f1"]), 4), "artefact": str(row.get("artefact") or "-")}
                for row in rows
            ]
        },
    }


def handle(method, path, payload, user):
    if method == "GET" and path.endswith("/runs"):
        return 200, {"runs": summary()["lists"]["runs"]}
    return 404, {"error": "not found"}
