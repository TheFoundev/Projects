"""Chunked groupby over partitioned input files."""
from pathlib import Path

import numpy as np
import pandas as pd


def write_partitions(base, chunks=4, rows_per_chunk=2000, seed=42):
    rng = np.random.default_rng(seed)
    input_dir = base / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    regions = np.array(["north", "south", "east", "west"])
    products = np.array(["widget", "gadget", "cable", "stand", "sensor"])
    for chunk in range(chunks):
        frame = pd.DataFrame({
            "order_id": np.arange(chunk * rows_per_chunk, (chunk + 1) * rows_per_chunk),
            "region": rng.choice(regions, rows_per_chunk),
            "product": rng.choice(products, rows_per_chunk),
            "quantity": rng.integers(1, 8, rows_per_chunk),
            "unit_price": np.round(rng.uniform(3, 45, rows_per_chunk), 2),
        })
        frame["revenue"] = (frame["quantity"] * frame["unit_price"]).round(2)
        frame.to_csv(input_dir / f"part-{chunk:03d}.csv", index=False)
    return sorted(input_dir.glob("part-*.csv"))


def run(quick=False, base_dir="artifacts"):
    base = Path(base_dir)
    base.mkdir(parents=True, exist_ok=True)
    files = write_partitions(base, 3 if quick else 12, 1500 if quick else 5000)
    partials = []
    total_rows = 0
    for path in files:
        frame = pd.read_csv(path)
        total_rows += len(frame)
        partial = (
            frame.groupby(["region", "product"])
            .agg(orders=("order_id", "count"), revenue=("revenue", "sum"))
            .reset_index()
        )
        partials.append(partial)

    combined = (
        pd.concat(partials, ignore_index=True)
        .groupby(["region", "product"], as_index=False)
        .agg(orders=("orders", "sum"), revenue=("revenue", "sum"))
    )
    combined["revenue"] = combined["revenue"].round(2)
    combined = combined.sort_values("revenue", ascending=False)
    output = base / "summary.parquet"
    try:
        combined.to_parquet(output, index=False)
        output_format = "parquet"
    except Exception:
        output = base / "summary.csv"
        combined.to_csv(output, index=False)
        output_format = "csv"

    top = combined.iloc[0]
    return {
        "input_rows": int(total_rows),
        "partitions": len(files),
        "rows_kept_in_memory": int(len(combined)),
        "top_region": str(top["region"]),
        "top_product": str(top["product"]),
        "total_revenue": round(float(combined["revenue"].sum()), 2),
        "output": str(output),
        "format": output_format,
    }


def demo(base_dir="artifacts"):
    summary = run(quick=True, base_dir=base_dir)
    print(f"Processed {summary['input_rows']} rows in {summary['partitions']} partitions.")
    print(f"Summary rows: {summary['rows_kept_in_memory']} ({summary['format']})")
    print(f"Top product: {summary['top_product']} in the {summary['top_region']} region.")
    sizes = [path.stat().st_size for path in sorted((Path(base_dir) / "input").glob("part-*.csv"))]
    print("Partition sizes (bytes):", sizes)
