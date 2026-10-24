"""The API of the crawler.

The numbers are the real ones: the site is written by the project, the
crawler of the project walks it and the index of the pages and the broken
links come out of that walk. The crawl is run inside the process that answers
the request, on a server of its own on the loopback interface, so no network
and no permission are needed.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.pipeline import run  # noqa: E402

#: The result of the last crawl, so a page does not crawl again for every call.
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


def _crawl(base_dir: str = "artifacts") -> dict:
    """The crawl of the site, with the index and the broken links."""
    key = str(base_dir)
    if key not in _CACHE:
        summary = run(quick=False, base_dir=base_dir)
        pages = []
        index = Path(base_dir) / "pages.jsonl"
        if index.exists():
            import json

            for line in index.read_text(encoding="utf-8").strip().splitlines():
                if line:
                    row = json.loads(line)
                    pages.append({
                        "page": row["url"],
                        "title": row["title"] or "(no title)",
                        "links": row["links"],
                    })
        broken = []
        broken_file = Path(base_dir) / "broken.txt"
        if broken_file.exists():
            for line in broken_file.read_text(encoding="utf-8").strip().splitlines():
                if line:
                    broken.append({"broken link": line})
        _CACHE[key] = {"summary": summary, "pages": pages, "broken": broken}
    return _CACHE[key]


def summary():
    state = _crawl()
    numbers = state["summary"]
    pages = state["pages"]

    return {
        "stats": {
            "crawled_pages": numbers["crawled_pages"],
            "links_seen": numbers["links_seen"],
            "broken_links": numbers["broken_links"],
            "generated_pages": numbers["generated_pages"],
        },
        "series": [
            {"label": row["title"], "value": row["links"]}
            for row in pages
        ],
        "lists": {
            "pages": pages,
            "broken": state["broken"],
        },
    }


def handle(method, path, payload, user):
    if method == "GET" and path == "/api/pages":
        return 200, {"pages": _crawl()["pages"]}

    if method == "GET" and path == "/api/broken":
        return 200, {"broken": _crawl()["broken"]}

    if method == "POST" and path == "/api/crawl":
        _CACHE.clear()
        state = summary()
        return 200, {"crawled": True, "summary": state}

    return 404, {"error": "not found"}
