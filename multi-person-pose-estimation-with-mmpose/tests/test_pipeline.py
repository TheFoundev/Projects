"""Tests for the pose estimation."""
import numpy as np

from src.data import load_data, make_scene
from src.model import demo, estimate, pck, train


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


def test_the_pck_of_the_truth_with_itself_is_one():
    scene = make_scene(seed=2)
    score, joints = pck(scene["joints"], scene["joints"])
    assert score == 1.0
    assert joints == 14


def test_the_pck_of_a_wrong_answer_is_low():
    scene = make_scene(seed=2)
    wrong = [joints + 100 for joints in scene["joints"]]
    score, _ = pck(wrong, scene["joints"])
    assert score < 0.5


def test_the_estimator_finds_the_people():
    scene = make_scene(seed=2)
    joints = estimate(scene["image"])
    assert len(joints) >= 1
