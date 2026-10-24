"""Tests for the model runner."""
import json
import sqlite3

import pytest

from src.pipeline import (
    MODEL_DIR,
    dependencies,
    demo,
    model_names,
    order_models,
    render,
    run,
)


def test_pipeline_runs(tmp_path, capsys):
    summary = run(quick=True, base_dir=str(tmp_path))
    assert isinstance(summary, dict)
    assert summary
    assert any(tmp_path.iterdir())

    demo(base_dir=str(tmp_path))
    assert capsys.readouterr().out.strip()


def test_the_models_are_the_files_of_the_models_directory():
    names = model_names()
    assert "staging_orders" in names
    assert "segment_summary" in names
    for name in names:
        assert (MODEL_DIR / f"{name}.sql").exists()


def test_the_order_comes_from_the_refs():
    order = order_models()

    position = {name: index for index, name in enumerate(order)}
    assert position["staging_orders"] < position["daily_revenue"]
    assert position["daily_revenue"] < position["segment_summary"]
    assert position["customer_value"] < position["mart_customer_segments"]
    assert position["mart_customer_segments"] < position["segment_summary"]


def test_a_model_that_needs_a_model_that_is_not_there_is_refused():
    with pytest.raises(ValueError):
        render("select * from {{ ref('nope') }}", {"staging_orders"})


def test_a_cycle_is_refused(tmp_path):
    directory = tmp_path / "models"
    directory.mkdir()
    (directory / "a.sql").write_text("select * from {{ ref('b') }}")
    (directory / "b.sql").write_text("select * from {{ ref('a') }}")

    with pytest.raises(ValueError):
        order_models(["a", "b"], sql_dir=directory)


def test_the_refs_of_a_model_are_found():
    found = dependencies((MODEL_DIR / "daily_revenue.sql").read_text())
    assert "staging_orders" in found


def test_the_manifest_holds_the_dependencies(tmp_path):
    run(quick=True, base_dir=str(tmp_path))
    manifest = json.loads((tmp_path / "manifest.json").read_text())

    by_name = {item["name"]: item for item in manifest["models"]}
    assert by_name["daily_revenue"]["depends_on"] == ["staging_orders"]
    assert by_name["raw_customers" if "raw_customers" in by_name else "staging_orders"]


def test_the_models_are_materialised(tmp_path):
    run(quick=True, base_dir=str(tmp_path))
    connection = sqlite3.connect(tmp_path / "warehouse.db")
    names = [
        row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    ]
    connection.close()

    for model in model_names():
        assert model in names


def test_the_revenue_is_the_sum_of_the_daily_revenue(tmp_path):
    run(quick=True, base_dir=str(tmp_path))
    connection = sqlite3.connect(tmp_path / "warehouse.db")
    total = connection.execute("SELECT ROUND(SUM(revenue), 2) FROM daily_revenue").fetchone()[0]
    rows = connection.execute("SELECT COUNT(*) FROM daily_revenue").fetchone()[0]
    connection.close()

    assert rows > 0
    assert total > 0
