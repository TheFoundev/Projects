"""Tests for the attribute kiosk."""
import numpy as np

from src.data import draw_face, load_data
from src.model import demo, train


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


def test_the_face_is_drawn_with_the_two_attributes():
    image, glasses, smiling = draw_face(seed=2, size=32)
    assert image.shape == (32, 32)
    assert glasses in (True, False)
    assert smiling in (True, False)


def test_the_two_attributes_are_measured():
    data = load_data(seed=4, quick=True)
    _, metrics = train(data, quick=True)
    assert 0 <= metrics["glasses_accuracy"] <= 1
    assert 0 <= metrics["smile_accuracy"] <= 1
    assert metrics["samples"] == len(data["X_test"])
