"""A four-task orders pipeline with a DAG definition.

The tasks are ordered by the graph in `DEPENDENCIES`, not by the order they
happen to be written in, and a task that fails is retried before the run is
given up on. Every task is a function of its own, so the Airflow DAG in
`dags/orders_dag.py` and the local runner do the same work.
"""
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

DAG_ID = "orders_etl"
SCHEDULE = "@daily"
TASKS = ["extract_orders", "validate_orders", "build_daily", "load_warehouse"]
DEPENDENCIES = {
    "extract_orders": [],
    "validate_orders": ["extract_orders"],
    "build_daily": ["validate_orders"],
    "load_warehouse": ["build_daily"],
}

#: How often a task is tried again before the run is given up on.
RETRIES = 2

#: How long a task waits before it is tried again, in seconds.
RETRY_BACKOFF = 0.2


class PipelineContext:
    """What the tasks share: the paths, the warehouse and the state."""

    def __init__(self, base, connection):
        self.base = Path(base)
        self.connection = connection
        self.state = {}

    @property
    def raw_path(self):
        return self.base / "raw" / "orders.csv"

    @property
    def clean_path(self):
        return self.base / "clean" / "orders_clean.csv"

    @property
    def daily_path(self):
        return self.base / "clean" / "daily_sales.csv"


def make_orders(count=240, seed=42):
    rng = np.random.default_rng(seed)
    start = pd.Timestamp("2026-01-01")
    return pd.DataFrame({
        "order_id": np.arange(1000, 1000 + count),
        "customer_id": rng.integers(1, 80, count),
        "order_ts": start + pd.to_timedelta(rng.integers(0, 30 * 24 * 60, count), unit="m"),
        "status": rng.choice(["paid", "paid", "paid", "pending", "refunded"], count),
        "quantity": rng.integers(1, 5, count),
        "unit_price": np.round(rng.uniform(8, 90, count), 2),
    })


def extract_orders(context):
    """Read the raw orders."""
    frame = pd.read_csv(context.raw_path)
    context.state["extracted"] = len(frame)
    return len(frame)


def validate_orders(context):
    """Keep the orders that are paid and add the revenue."""
    frame = pd.read_csv(context.raw_path)
    clean = frame[
        (frame["status"] == "paid")
        & (frame["quantity"] > 0)
        & frame["customer_id"].notna()
    ].copy()
    clean["revenue"] = (clean["quantity"] * clean["unit_price"]).round(2)
    clean["order_date"] = pd.to_datetime(clean["order_ts"]).dt.date.astype(str)
    clean.to_csv(context.clean_path, index=False)
    context.state["clean"] = clean
    return len(clean)


def build_daily(context):
    """The revenue of every day."""
    clean = context.state["clean"]
    daily = (
        clean.groupby("order_date")
        .agg(orders=("order_id", "count"), revenue=("revenue", "sum"))
        .reset_index()
    )
    daily["revenue"] = daily["revenue"].round(2)
    daily.to_csv(context.daily_path, index=False)
    context.state["daily"] = daily
    return len(daily)


def load_warehouse(context):
    """Write the clean orders and the daily revenue into the warehouse."""
    context.state["clean"].to_sql("clean_orders", context.connection, if_exists="replace", index=False)
    context.state["daily"].to_sql("daily_sales", context.connection, if_exists="replace", index=False)
    context.connection.commit()
    return len(context.state["daily"])


#: The tasks of the pipeline, by name.
FUNCTIONS = {
    "extract_orders": extract_orders,
    "validate_orders": validate_orders,
    "build_daily": build_daily,
    "load_warehouse": load_warehouse,
}


def order_tasks(tasks=None, dependencies=None):
    """The tasks in the order they have to run.

    The order comes from the dependency graph, so a task only runs after the
    tasks it needs. A task that needs a task that is not in the pipeline, and
    a cycle, are errors.
    """
    tasks = list(tasks or TASKS)
    dependencies = dependencies or DEPENDENCIES

    by_name = {task: list(dependencies.get(task, [])) for task in tasks}
    for task, needs in by_name.items():
        for need in needs:
            if need not in by_name:
                raise ValueError(f"the task {task!r} needs {need!r}, which is not in the pipeline")

    ordered = []
    done = set()
    while len(ordered) < len(tasks):
        progress = False
        for task in tasks:
            if task in done:
                continue
            if all(need in done for need in by_name[task]):
                ordered.append(task)
                done.add(task)
                progress = True
        if not progress:
            raise ValueError("the pipeline has a cycle")

    return ordered


def run(quick=False, base_dir="artifacts", retries=RETRIES):
    """Run the pipeline."""
    base = Path(base_dir)
    (base / "raw").mkdir(parents=True, exist_ok=True)
    (base / "clean").mkdir(parents=True, exist_ok=True)
    orders = make_orders(240 if quick else 1500)
    orders.to_csv(base / "raw" / "orders.csv", index=False)

    connection = sqlite3.connect(base / "warehouse.db")
    connection.execute(
        "CREATE TABLE IF NOT EXISTS task_runs ("
        "task TEXT, status TEXT, rows INTEGER, seconds REAL, finished_at TEXT)"
    )
    connection.commit()

    context = PipelineContext(base, connection)
    context.state["raw"] = len(orders)
    statuses = []
    attempts = {}
    order = order_tasks()

    for index, task in enumerate(order):
        started = time.perf_counter()
        rows = 0
        status = "failed"
        error = None

        for attempt in range(1, retries + 2):
            attempts[task] = attempt
            try:
                rows = FUNCTIONS[task](context)
                status = "success"
                break
            except Exception as failure:  # noqa: BLE001 - the run has to carry on
                error = failure
                if attempt <= retries:
                    time.sleep(RETRY_BACKOFF)

        connection.execute(
            "INSERT INTO task_runs VALUES (?, ?, ?, ?, ?)",
            (task, status, int(rows), time.perf_counter() - started,
             datetime.now(timezone.utc).isoformat(timespec="seconds")),
        )
        connection.commit()

        if status != "success":
            # The tasks that already ran are marked as rolled back, so the
            # history shows what happened to the whole run.
            for done_task in order[:index]:
                connection.execute(
                    "INSERT INTO task_runs VALUES (?, ?, ?, ?, ?)",
                    (done_task, "rolled_back", 0, 0.0,
                     datetime.now(timezone.utc).isoformat(timespec="seconds")),
                )
            connection.commit()
            connection.close()
            raise error

        statuses.append(status)

    connection.close()
    return {
        "dag_id": DAG_ID,
        "schedule": SCHEDULE,
        "tasks": len(TASKS),
        "order": order,
        "raw_rows": int(len(orders)),
        "clean_rows": int(len(context.state["clean"])),
        "daily_rows": int(len(context.state["daily"])),
        "attempts": attempts,
        "warehouse": str(base / "warehouse.db"),
    }


def demo(base_dir="artifacts"):
    summary = run(quick=True, base_dir=base_dir)
    print(f"DAG {summary['dag_id']} ({summary['schedule']})")
    for task in summary["order"]:
        print(f"  {task:16s} requires={DEPENDENCIES[task]}")
    print(f"Raw rows: {summary['raw_rows']}, clean rows: {summary['clean_rows']}, daily rows: {summary['daily_rows']}")
    daily = pd.read_csv(Path(base_dir) / "clean" / "daily_sales.csv")
    print(daily.head(3).to_string(index=False))
