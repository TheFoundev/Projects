"""Tests for the experiment registry."""
import sqlite3

from src.data import load_data
from src.model import best_run, candidates, demo, ensure_db, train


def test_pipeline_runs(capsys):
    data = load_data(seed=1, quick=True)
    assert data is not None

    model, metrics = train(data, quick=True)
    assert model is not None
    assert isinstance(metrics, dict) and metrics

    for value in metrics.values():
        if isinstance(value, bool):
            continue
        assert value is None or isinstance(value, (int, float, str))

    demo(data)
    assert capsys.readouterr().out.strip()


def test_seed_is_usable():
    first = load_data(seed=3, quick=True)
    second = load_data(seed=3, quick=True)
    assert first.keys() == second.keys()


def test_there_are_several_candidates():
    options = candidates(quick=True)
    assert len(options) >= 3
    for name, model in options.items():
        assert hasattr(model, "fit")


def test_the_runs_are_stored(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data = load_data(seed=2, quick=True)
    model, metrics = train(data, quick=True)

    connection = sqlite3.connect(tmp_path / "artifacts" / "registry.db")
    rows = connection.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    connection.close()
    assert rows >= 1
