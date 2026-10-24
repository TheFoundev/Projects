"""The API of the project: the models of the run and the manifest.

The numbers come from a real run of the runner: the raw tables are loaded
into SQLite, every model is rendered with its refs replaced by the tables
that are already there, and the manifest of the run is written next to the
warehouse.
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.pipeline import run  # noqa: E402

#: Where the runner writes the warehouse and the manifest.
BASE_DIR = ROOT / "artifacts"
MANIFEST = BASE_DIR / "manifest.json"
WAREHOUSE = BASE_DIR / "warehouse.db"

#: The summary of the last run, kept for the life of the process.
_STATE: dict = {}


def state() -> dict:
    """Materialise the models and keep the manifest of the run."""
    if "run" not in _STATE:
        result = run(quick=False, base_dir=str(BASE_DIR))
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        _STATE["run"] = result
        _STATE["manifest"] = manifest
    return _STATE


def models() -> list:
    """The models of the run, with the models they need and their rows."""
    return [
        {
            "model": model["name"],
            "needs": ", ".join(model["depends_on"]) or "-",
            "rows": model["rows"],
        }
        for model in state()["manifest"]["models"]
    ]


def raw_tables() -> list:
    """The tables the models are built from, with the rows they hold."""
    if not WAREHOUSE.exists():
        return []
    connection = sqlite3.connect(WAREHOUSE)
    rows = []
    for table in state()["manifest"]["raw_tables"]:
        count = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        rows.append({"table": table, "rows": int(count)})
    connection.close()
    return rows


def summary() -> dict:
    """The state of the last run: the models, the raw orders and the revenue."""
    current = state()
    result = current["run"]
    built = current["manifest"]["models"]
    return {
        "stats": {
            "models": result["models"],
            "raw_orders": result["raw_orders"],
            "staging_rows": result["staging_rows"],
            "revenue": result["revenue"],
        },
        "series": [
            {"label": model["name"], "value": model["rows"]} for model in built
        ],
        "lists": {
            "models": models(),
            "raw_tables": raw_tables(),
        },
    }


def handle(method, path, payload, user):
    """The read and the write endpoints of the project."""
    if method == "GET" and path == "/api/models":
        return 200, {"models": models()}
    if method == "GET" and path == "/api/manifest":
        return 200, state()["manifest"]
    if method == "POST" and path == "/api/run":
        _STATE.pop("run", None)
        _STATE.pop("manifest", None)
        state()
        return 200, summary()["stats"]
    return 404, {"error": "not found"}
