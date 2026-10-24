"""Tests for the anomaly detection."""
import numpy as np

from src.data import load_data
from src.model import demo, evaluate, simulate, train


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


def test_the_flags_have_the_size_of_the_stream():
    values = np.concatenate([np.zeros(100), np.ones(10) * 5])
    _, flags = simulate(values)
    assert len(flags) == len(values)


def test_the_spike_is_found():
    values = np.concatenate([np.zeros(100), np.ones(5) * 6])
    _, flags = simulate(values)
    assert flags[-5:].sum() >= 1, "the spike at the end has to be found"


def test_the_metrics_are_shares():
    labels = np.array([0, 0, 1, 1])
    flags = np.array([0, 1, 1, 0])
    precision, recall, f1 = evaluate(labels, flags)
    assert 0 <= precision <= 1
    assert 0 <= recall <= 1
    assert 0 <= f1 <= 1
