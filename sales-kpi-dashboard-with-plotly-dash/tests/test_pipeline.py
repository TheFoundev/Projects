"""Tests for the KPI dashboard."""
import pandas as pd

from src.pipeline import demo, make_sales, run


def test_pipeline_runs(tmp_path, capsys):
    summary = run(quick=True, base_dir=str(tmp_path))
    assert isinstance(summary, dict)
    assert summary
    assert any(tmp_path.iterdir())

    demo(base_dir=str(tmp_path))
    assert capsys.readouterr().out.strip()


def test_the_sales_are_made():
    frame = make_sales(count=30, seed=1)
    assert len(frame) == 30
    assert "revenue" in frame.columns
    assert "order_date" in frame.columns


def test_the_numbers_are_worked_out(tmp_path):
    summary = run(quick=True, base_dir=str(tmp_path))
    assert summary["revenue"] > 0
    assert summary["orders"] > 0
