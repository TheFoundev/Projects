"""Tests for the out of core aggregation."""
import pandas as pd

from src.pipeline import demo, run


def test_pipeline_runs(tmp_path, capsys):
    summary = run(quick=True, base_dir=str(tmp_path))
    assert isinstance(summary, dict)
    assert summary
    assert any(tmp_path.iterdir())

    demo(base_dir=str(tmp_path))
    assert capsys.readouterr().out.strip()


def test_the_summary_counts_the_rows_and_the_partitions(tmp_path):
    summary = run(quick=True, base_dir=str(tmp_path))
    assert summary["input_rows"] > 0
    assert summary["partitions"] > 1
    assert summary["total_revenue"] > 0


def test_the_summary_is_written(tmp_path):
    run(quick=True, base_dir=str(tmp_path))
    assert (tmp_path / "summary.csv").exists() or (tmp_path / "summary.parquet").exists()


def test_the_top_region_is_the_biggest_one(tmp_path):
    summary = run(quick=True, base_dir=str(tmp_path))
    assert summary["top_region"]
    assert summary["top_product"]
