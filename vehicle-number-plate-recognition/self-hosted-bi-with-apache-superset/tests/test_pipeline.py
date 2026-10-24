"""Tests for the BI dashboard."""
import pandas as pd

from src.pipeline import demo, make_orders, run


def test_pipeline_runs(tmp_path, capsys):
    summary = run(quick=True, base_dir=str(tmp_path))
    assert isinstance(summary, dict)
    assert summary
    assert any(tmp_path.iterdir())

    demo(base_dir=str(tmp_path))
    assert capsys.readouterr().out.strip()


def test_the_orders_are_made():
    frame = make_orders(count=40, seed=2)
    assert len(frame) == 40


def test_the_numbers_are_worked_out(tmp_path):
    summary = run(quick=True, base_dir=str(tmp_path))
    assert summary["orders"] > 0
    assert summary["revenue"] > 0


def test_the_dashboard_is_saved(tmp_path):
    run(quick=True, base_dir=str(tmp_path))
    assert (tmp_path / "dashboard.json").exists()
