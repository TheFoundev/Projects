"""The API of the SSH audit.

The numbers are the real ones: a server of the project is started on the
loopback interface, the audit of the project connects to it, reads the banner
and the key exchange packet and looks at every algorithm it offers. The score
and the grade come out of that audit, so the console shows the report of a
real handshake and not of a table of constants.
"""

import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.pipeline import audit, make_server  # noqa: E402

#: The report of the last audit, so a page does not audit again for every call.
_CACHE: dict[str, dict] = {}


def _number(payload, key: str, default: int) -> int:
    """One number of the request.

    The query string of a GET arrives as a dictionary of lists, so the first
    value of the list is taken.
    """
    value = (payload or {}).get(key, default)
    if isinstance(value, (list, tuple)):
        value = value[0] if value else default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _audit(good: bool) -> dict:
    """The audit of a server of the project.

    The server is started on a port of its own, the audit connects to it and
    the report is put together from what the handshake really said.
    """
    ready: list[int] = []
    thread = threading.Thread(target=make_server(good=good), args=(ready,), daemon=True)
    thread.start()
    for _ in range(100):
        if ready:
            break
        threading.Event().wait(0.05)
    try:
        banner, algorithms, findings, score, grade = audit(ready[0])
    finally:
        thread.join(timeout=2)
    return {
        "banner": banner,
        "server": banner.split("-")[-1] if "-" in banner else banner,
        "algorithms": algorithms,
        "findings": findings,
        "score": score,
        "grade": grade,
    }


def _report(good: bool = False) -> dict:
    key = "good" if good else "weak"
    if key not in _CACHE:
        _CACHE[key] = _audit(good)
    return _CACHE[key]


def summary():
    report = _report(good=False)
    good = _report(good=True)

    return {
        "stats": {
            "score": report["score"],
            "grade": report["grade"],
            "weak_findings": len(report["findings"]),
            "groups": len(report["algorithms"]),
        },
        "series": [
            {"label": "modern server", "value": good["score"]},
            {"label": "weak server", "value": report["score"]},
        ],
        "lists": {
            "findings": [
                {"group": finding["group"], "algorithm": finding["algorithm"]}
                for finding in report["findings"]
            ],
            "algorithms": [
                {"group": group, "algorithms": ", ".join(values)}
                for group, values in report["algorithms"].items()
            ],
        },
    }


def handle(method, path, payload, user):
    if method == "GET" and path == "/api/algorithms":
        return 200, {"algorithms": summary()["lists"]["algorithms"]}

    if method == "GET" and path == "/api/findings":
        return 200, {"findings": summary()["lists"]["findings"]}

    if method == "POST" and path == "/api/audit":
        _CACHE.clear()
        state = summary()
        return 200, {"audited": True, "summary": state}

    return 404, {"error": "not found"}
