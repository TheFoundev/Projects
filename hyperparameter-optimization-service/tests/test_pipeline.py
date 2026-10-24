"""Tests for the hyperparameter search."""
import json
import sqlite3

from src.data import load_data
from src.model import demo, ensure_db, run_search, train


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


def test_the_trials_are_written_in_the_database(tmp_path):
    path = tmp_path / "trials.db"
    data = load_data(seed=2, quick=True)
    _, summary = run_search(data, trials=4, db_path=str(path))

    assert summary["trials_this_run"] == 4
    connection = sqlite3.connect(path)
    rows = connection.execute("SELECT COUNT(*) FROM trials").fetchone()[0]
    connection.close()
    assert rows == 4


def test_the_trials_of_the_runs_add_up(tmp_path):
    path = tmp_path / "trials.db"
    data = load_data(seed=2, quick=True)
    run_search(data, trials=3, db_path=str(path))
    _, summary = run_search(data, trials=2, db_path=str(path))

    assert summary["trials_total"] == 5
    assert summary["trials_this_run"] == 2


def test_the_best_trial_is_the_one_with_the_best_score(tmp_path):
    path = tmp_path / "trials.db"
    data = load_data(seed=2, quick=True)
    _, summary = run_search(data, trials=4, db_path=str(path))

    connection = sqlite3.connect(path)
    top = connection.execute(
        "SELECT accuracy FROM trials ORDER BY accuracy DESC LIMIT 1"
    ).fetchone()[0]
    connection.close()

    assert summary["best_accuracy"] >= top - 1e-9
    assert summary["best_params"]


def test_the_database_is_created_when_it_is_not_there(tmp_path):
    path = tmp_path / "nested" / "trials.db"
    ensure_db(str(path))
    assert path.exists()
