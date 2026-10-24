"""Tests for the orders pipeline."""
import sqlite3

import pandas as pd
import pytest

from src.pipeline import (
    DEPENDENCIES,
    TASKS,
    FUNCTIONS,
    build_daily,
    extract_orders,
    load_warehouse,
    make_orders,
    order_tasks,
    run,
    validate_orders,
    demo,
)


def test_pipeline_runs(tmp_path, capsys):
    summary = run(quick=True, base_dir=str(tmp_path))
    assert isinstance(summary, dict)
    assert summary
    assert any(tmp_path.iterdir())

    demo(base_dir=str(tmp_path))
    assert capsys.readouterr().out.strip()


# ---------------------------------------------------------------------------
# The order of the tasks
# ---------------------------------------------------------------------------

def test_the_order_comes_from_the_dependencies():
    order = order_tasks()
    assert order.index("extract_orders") < order.index("validate_orders")
    assert order.index("validate_orders") < order.index("build_daily")
    assert order.index("build_daily") < order.index("load_warehouse")


def test_the_order_follows_the_graph_even_when_the_tasks_are_written_in_another_order():
    tasks = ["load_warehouse", "build_daily", "validate_orders", "extract_orders"]
    order = order_tasks(tasks, DEPENDENCIES)
    assert order[0] == "extract_orders"
    assert order[-1] == "load_warehouse"


def test_a_task_that_needs_a_task_that_is_not_there_is_refused():
    with pytest.raises(ValueError):
        order_tasks(["a"], {"a": ["b"]})


def test_a_cycle_is_refused():
    with pytest.raises(ValueError):
        order_tasks(["a", "b"], {"a": ["b"], "b": ["a"]})


# ---------------------------------------------------------------------------
# What the pipeline writes
# ---------------------------------------------------------------------------

def test_the_pipeline_writes_the_files(tmp_path):
    summary = run(quick=True, base_dir=str(tmp_path))

    assert (tmp_path / "raw" / "orders.csv").exists()
    assert (tmp_path / "clean" / "orders_clean.csv").exists()
    assert (tmp_path / "clean" / "daily_sales.csv").exists()
    assert summary["clean_rows"] <= summary["raw_rows"]
    assert summary["daily_rows"] > 0


def test_the_clean_orders_are_the_paid_ones(tmp_path):
    run(quick=True, base_dir=str(tmp_path))
    raw = pd.read_csv(tmp_path / "raw" / "orders.csv")
    clean = pd.read_csv(tmp_path / "clean" / "orders_clean.csv")

    assert len(clean) == len(raw[raw["status"] == "paid"])
    assert (clean["revenue"] > 0).all()
    assert (clean["quantity"] > 0).all()


def test_the_revenue_of_the_day_is_the_sum_of_its_orders(tmp_path):
    run(quick=True, base_dir=str(tmp_path))
    clean = pd.read_csv(tmp_path / "clean" / "orders_clean.csv")
    daily = pd.read_csv(tmp_path / "clean" / "daily_sales.csv")

    expected = clean.groupby("order_date")["revenue"].sum().round(2)
    for _, row in daily.iterrows():
        assert round(row["revenue"], 2) == round(expected[row["order_date"]], 2)


def test_the_warehouse_holds_the_tables(tmp_path):
    run(quick=True, base_dir=str(tmp_path))
    connection = sqlite3.connect(tmp_path / "warehouse.db")

    runs = connection.execute("SELECT task, status, rows FROM task_runs").fetchall()
    assert len(runs) == len(TASKS)
    assert all(row[1] == "success" for row in runs)

    daily = connection.execute("SELECT COUNT(*) FROM daily_sales").fetchone()[0]
    clean = connection.execute("SELECT COUNT(*) FROM clean_orders").fetchone()[0]
    connection.close()

    assert daily > 0
    assert clean > 0


def test_the_history_holds_the_time_of_every_task(tmp_path):
    run(quick=True, base_dir=str(tmp_path))
    connection = sqlite3.connect(tmp_path / "warehouse.db")
    rows = connection.execute("SELECT task, seconds, finished_at FROM task_runs").fetchall()
    connection.close()

    assert all(row[2] for row in rows)
    assert all(row[1] >= 0 for row in rows)


# ---------------------------------------------------------------------------
# The failure path
# ---------------------------------------------------------------------------

def test_a_failing_task_is_retried_and_the_run_is_given_up_on(tmp_path, monkeypatch):
    calls = {"count": 0}

    def broken(context):
        calls["count"] += 1
        raise RuntimeError("the warehouse is not there")

    monkeypatch.setitem(FUNCTIONS, "build_daily", broken)

    with pytest.raises(RuntimeError):
        run(quick=True, base_dir=str(tmp_path), retries=2)

    # The task was tried three times: the first try and the two retries.
    assert calls["count"] == 3


def test_the_tasks_that_ran_are_marked_when_a_task_fails(tmp_path, monkeypatch):
    def broken(context):
        raise RuntimeError("the warehouse is not there")

    monkeypatch.setitem(FUNCTIONS, "build_daily", broken)

    with pytest.raises(RuntimeError):
        run(quick=True, base_dir=str(tmp_path), retries=0)

    connection = sqlite3.connect(tmp_path / "warehouse.db")
    rows = connection.execute("SELECT task, status FROM task_runs").fetchall()
    connection.close()

    statuses = dict(rows)
    assert statuses["build_daily"] == "failed"
    assert statuses["extract_orders"] == "rolled_back"


def test_a_task_that_works_the_second_time_carries_on(tmp_path, monkeypatch):
    original = FUNCTIONS["build_daily"]
    calls = {"count": 0}

    def flaky(context):
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("not yet")
        return original(context)

    monkeypatch.setitem(FUNCTIONS, "build_daily", flaky)

    summary = run(quick=True, base_dir=str(tmp_path), retries=2)
    assert summary["attempts"]["build_daily"] == 2
    assert summary["daily_rows"] > 0
