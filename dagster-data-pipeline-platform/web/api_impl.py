"""The API of the project: the assets of the graph and the RFM groups.

The numbers come from a real run of the asset graph: the assets are
materialised as Parquet files and every materialisation is written into the
lineage log of the run, which is where the console reads them from.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.pipeline import ASSET_GRAPH, run  # noqa: E402

#: Where the assets and the lineage log of the run are written.
BASE_DIR = ROOT / "artifacts"
LINEAGE = BASE_DIR / "lineage.db"
WAREHOUSE = BASE_DIR / "warehouse"

#: The summary of the last run, kept for the life of the process.
_STATE: dict = {}


def state() -> dict:
    """Materialise the assets and keep the summary of the run."""
    if "run" not in _STATE:
        result = run(quick=False, base_dir=str(BASE_DIR))
        _STATE["run"] = result
        _STATE["assets"] = assets(result["run_id"])
        _STATE["segments"] = segments()
    return _STATE


def assets(run_id: str) -> list:
    """The assets of the run, with the assets they need and their rows."""
    if not LINEAGE.exists():
        return []
    connection = sqlite3.connect(LINEAGE)
    rows = connection.execute(
        "SELECT asset, upstream, rows, materialized_at FROM materializations "
        "WHERE run_id = ? ORDER BY rowid",
        (run_id,),
    ).fetchall()
    connection.close()
    return [
        {
            "asset": row[0],
            "needs": row[1] or "-",
            "rows": row[2],
            "run": run_id,
        }
        for row in rows
    ]


def segments() -> list:
    """The RFM groups with the number of the customers and what they are worth."""
    path = WAREHOUSE / "segment_report.parquet"
    if not path.exists():
        return []
    report = pd.read_parquet(path)
    return [
        {
            "group": row["rfm_group"],
            "customers": int(row["customers"]),
            "avg_value": round(float(row["avg_annual_value"]), 2),
        }
        for _, row in report.iterrows()
    ]


def summary() -> dict:
    """The state of the last run: the assets, the customers and the groups."""
    current = state()
    result = current["run"]
    groups = current["segments"]
    return {
        "stats": {
            "assets": result["assets"],
            "customers": result["customers"],
            "segments": result["segments"],
            "high_value_customers": result["high_value_customers"],
        },
        "series": [
            {"label": group["group"], "value": group["customers"]} for group in groups
        ],
        "lists": {
            "assets": current["assets"],
            "segments": groups,
        },
    }


def handle(method, path, payload, user):
    """The read and the write endpoints of the project."""
    if method == "GET" and path == "/api/assets":
        return 200, {"assets": state()["assets"]}
    if method == "GET" and path == "/api/segments":
        return 200, {"segments": state()["segments"]}
    if method == "POST" and path == "/api/materialise":
        _STATE.pop("run", None)
        _STATE.pop("assets", None)
        _STATE.pop("segments", None)
        state()
        return 200, summary()["stats"]
    return 404, {"error": "not found"}
