"""The API of the out-of-core aggregation.

The pipeline of the project really runs: the orders are written as
partitioned CSV files, every partition is read on its own, the group-by is
done per partition and the partial results are merged, so only the small
summary is held in memory. The console reads that summary back from the file
the pipeline wrote.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from src.pipeline import run  # noqa: E402

#: The directory the pipeline writes to.
BASE = ROOT / "artifacts"


def _number(payload, key: str, default: int) -> int:
    """One number of the request; a query string arrives as a list."""
    value = (payload or {}).get(key, default)
    if isinstance(value, (list, tuple)):
        value = value[0] if value else default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _read_summary() -> pd.DataFrame:
    """The merged summary the pipeline wrote to disk."""
    parquet = BASE / "summary.parquet"
    if parquet.exists():
        return pd.read_parquet(parquet)
    csv = BASE / "summary.csv"
    if csv.exists():
        return pd.read_csv(csv)
    return pd.DataFrame(columns=["region", "product", "orders", "revenue"])


def _partitions() -> list[dict]:
    """The input partitions with their rows and their size on disk."""
    rows = []
    for path in sorted((BASE / "input").glob("part-*.csv")):
        with path.open() as handle:
            lines = sum(1 for _ in handle) - 1
        rows.append({"partition": path.name, "rows": lines,
                     "bytes": path.stat().st_size})
    return rows


def summary():
    result = run(quick=False, base_dir=str(BASE))
    frame = _read_summary()

    # The revenue per region, summed over the products of the region.
    per_region = frame.groupby("region")["revenue"].sum().sort_values(ascending=False)

    return {
        "stats": {
            "input_rows": result["input_rows"],
            "partitions": result["partitions"],
            "rows_in_memory": result["rows_kept_in_memory"],
            "total_revenue": result["total_revenue"],
        },
        "series": [{"label": str(region), "value": round(float(value), 2)}
                   for region, value in per_region.items()],
        "lists": {
            "summary": [
                {"region": str(row["region"]), "product": str(row["product"]),
                 "orders": int(row["orders"]), "revenue": round(float(row["revenue"]), 2)}
                for _, row in frame.head(10).iterrows()
            ],
            "partitions": _partitions(),
        },
    }


def handle(method, path, payload, user):
    if method == "POST" and path == "/api/run":
        quick = bool((payload or {}).get("quick", False))
        result = run(quick=quick, base_dir=str(BASE))
        return 200, {"run": result, "summary": summary()}

    return 404, {"error": "not found"}
