"""The API of the project: the checks of the gate and the rows they rejected.

The numbers come from a real run of the gate: the checks are run over the
messy customer export, the report is written and the rows of the critical
checks are thrown away, so the report and the cleaned table always agree.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.pipeline import run  # noqa: E402

#: Where the gate writes the raw table, the clean one and the report.
BASE_DIR = ROOT / "artifacts"
REPORT = BASE_DIR / "quality_report.json"

#: The summary of the last run, kept for the life of the process.
_STATE: dict = {}


def state() -> dict:
    """Run the gate and keep the report of the run."""
    if "run" not in _STATE:
        result = run(quick=False, base_dir=str(BASE_DIR))
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        _STATE["run"] = result
        _STATE["report"] = report
    return _STATE


def checks() -> list:
    """Every check of the gate with its severity and its failures."""
    return [
        {
            "check": check["name"],
            "severity": check["severity"],
            "failures": check["failures"],
            "state": "ok" if check["passed"] else "failed",
        }
        for check in state()["report"]["checks"]
    ]


def failures() -> list:
    """The rows that failed a check, with the checks they failed."""
    return [
        {
            "customer": row["customer_id"],
            "checks": ", ".join(row["checks"]),
        }
        for row in state()["report"]["failed_rows"]
    ]


def summary() -> dict:
    """The state of the last gate: the rows, the clean rows and the failures."""
    current = state()
    result = current["run"]
    all_checks = current["report"]["checks"]
    return {
        "stats": {
            "rows": result["rows"],
            "clean_rows": result["clean_rows"],
            "critical_failures": result["critical_failures"],
            "warning_failures": result["warning_failures"],
        },
        "series": [
            {"label": check["name"], "value": check["failures"]} for check in all_checks
        ],
        "lists": {
            "checks": checks(),
            "failures": failures(),
        },
    }


def handle(method, path, payload, user):
    """The read and the write endpoints of the project."""
    if method == "GET" and path == "/api/checks":
        return 200, {"checks": checks()}
    if method == "GET" and path == "/api/failures":
        return 200, {"failures": failures()}
    if method == "POST" and path == "/api/run":
        _STATE.pop("run", None)
        _STATE.pop("report", None)
        state()
        return 200, summary()["stats"]
    return 404, {"error": "not found"}
