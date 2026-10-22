"""Tests for the batch pipeline."""
import pandas as pd

from src.pipeline import Aggregate, Clean, Extract, Load, Task, demo, execute, run


def test_pipeline_runs(tmp_path, capsys):
    summary = run(quick=True, base_dir=str(tmp_path))
    assert isinstance(summary, dict)
    assert summary
    assert any(tmp_path.iterdir())

    demo(base_dir=str(tmp_path))
    assert capsys.readouterr().out.strip()


def test_a_task_knows_what_it_needs_and_where_its_output_is(tmp_path):
    task = Extract(base=str(tmp_path))
    assert isinstance(task.requires(), list)
    assert "extract" in str(task.output())


def test_the_tasks_run_in_the_order_of_the_dependencies(tmp_path):
    done = []
    execute(Load(base=str(tmp_path)), done)
    assert done == ["extract", "clean", "aggregate", "load"]


def test_a_task_runs_the_tasks_it_needs_first(tmp_path):
    done = []
    execute(Aggregate(base=str(tmp_path)), done)
    assert done.index("extract") < done.index("clean") < done.index("aggregate")


def test_every_task_writes_its_marker(tmp_path):
    done = []
    execute(Load(base=str(tmp_path)), done)
    for name in done:
        assert list(tmp_path.rglob(f"{name}/done.json"))


def test_the_output_is_written(tmp_path):
    run(quick=True, base_dir=str(tmp_path))
    assert (tmp_path / "warehouse.db").exists()
