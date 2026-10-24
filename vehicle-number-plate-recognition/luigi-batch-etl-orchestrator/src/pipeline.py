"""Task objects with requires/output/run methods."""
import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


class Task:
    name = "task"

    def __init__(self, base, quick=False):
        self.base = Path(base)
        self.quick = quick

    def requires(self):
        return []

    def output(self):
        return self.base / self.name / "done.json"

    def run(self):
        raise NotImplementedError

    def __repr__(self):
        return f"<{self.name}>"


class Extract(Task):
    name = "extract"

    def run(self):
        rng = np.random.default_rng(11)
        count = 120 if self.quick else 600
        frame = pd.DataFrame({
            "order_id": np.arange(1, count + 1),
            "category": rng.choice(["books", "tools", "garden", "kitchen"], count),
            "quantity": rng.integers(1, 6, count),
            "unit_price": np.round(rng.uniform(4, 55, count), 2),
        })
        target = self.base / "extract" / "orders.csv"
        target.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(target, index=False)
        return int(len(frame))


class Clean(Task):
    name = "clean"

    def requires(self):
        return [Extract(self.base, self.quick)]

    def run(self):
        frame = pd.read_csv(self.base / "extract" / "orders.csv")
        frame = frame[(frame["quantity"] > 0) & (frame["unit_price"] > 0)].copy()
        frame["revenue"] = (frame["quantity"] * frame["unit_price"]).round(2)
        target = self.base / "clean" / "orders_clean.csv"
        target.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(target, index=False)
        return int(len(frame))


class Aggregate(Task):
    name = "aggregate"

    def requires(self):
        return [Clean(self.base, self.quick)]

    def run(self):
        frame = pd.read_csv(self.base / "clean" / "orders_clean.csv")
        summary = (
            frame.groupby("category")
            .agg(orders=("order_id", "count"), units=("quantity", "sum"), revenue=("revenue", "sum"))
            .reset_index()
        )
        summary["revenue"] = summary["revenue"].round(2)
        target = self.base / "aggregate" / "category_summary.csv"
        target.parent.mkdir(parents=True, exist_ok=True)
        summary.to_csv(target, index=False)
        return int(len(summary))


class Load(Task):
    name = "load"

    def requires(self):
        return [Aggregate(self.base, self.quick)]

    def run(self):
        frame = pd.read_csv(self.base / "aggregate" / "category_summary.csv")
        connection = sqlite3.connect(self.base / "warehouse.db")
        frame.to_sql("category_summary", connection, if_exists="replace", index=False)
        connection.commit()
        connection.close()
        return int(len(frame))


def execute(task, executed):
    for dependency in task.requires():
        execute(dependency, executed)
    rows = task.run()
    marker = task.output()
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(json.dumps({"task": task.name, "rows": int(rows)}), encoding="utf-8")
    executed.append(task.name)
    return rows


def run(quick=False, base_dir="artifacts"):
    base = Path(base_dir)
    base.mkdir(parents=True, exist_ok=True)
    target = Load(base, quick)
    executed = []
    rows = execute(target, executed)
    raw_rows = json.loads((base / "extract" / "done.json").read_text())["rows"]
    clean_rows = json.loads((base / "clean" / "done.json").read_text())["rows"]
    summary = pd.read_csv(base / "aggregate" / "category_summary.csv")
    return {
        "tasks_executed": len(executed),
        "task_order": ",".join(executed),
        "raw_rows": int(raw_rows),
        "clean_rows": int(clean_rows),
        "categories": int(rows),
        "revenue": round(float(summary["revenue"].sum()), 2),
    }


def demo(base_dir="artifacts"):
    summary = run(quick=True, base_dir=base_dir)
    chain = " -> ".join(summary["task_order"].split(","))
    print("Task chain:", chain)
    print(f"Raw rows: {summary['raw_rows']}, clean rows: {summary['clean_rows']}")
    summary_frame = pd.read_csv(Path(base_dir) / "aggregate" / "category_summary.csv")
    print(summary_frame.to_string(index=False))
