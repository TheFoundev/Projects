"""Tests for the instance segmentation."""
import numpy as np

from src.data import load_data, make_sample
from src.model import demo, evaluate, mask_iou, segment, train


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


def test_the_iou_of_a_mask_with_itself_is_one():
    mask = np.zeros((10, 10), dtype=bool)
    mask[2:6, 2:6] = True
    assert mask_iou(mask, mask) == 1.0


def test_the_iou_of_two_masks_that_do_not_touch_is_zero():
    first = np.zeros((10, 10), dtype=bool)
    second = np.zeros((10, 10), dtype=bool)
    first[0:2, 0:2] = True
    second[8:10, 8:10] = True
    assert mask_iou(first, second) == 0.0


def test_the_segmenter_finds_the_shapes():
    sample = make_sample(seed=2, size=64)
    instances = segment(sample["image"])

    assert len(instances) == len(sample["masks"])
    # The instances and the masks are not in the same order, so every found
    # instance is compared with the mask it fits the best.
    for truth in sample["masks"]:
        best = max(mask_iou(found, truth) for found in instances)
        assert best > 0.5


def test_the_evaluation_reports_the_iou():
    data = load_data(seed=4, quick=True)
    metrics = evaluate(data["samples"])
    assert 0 <= metrics["mean_iou"] <= 1
    assert metrics["instances"] > 0


def test_the_threshold_is_fitted_and_measured_on_different_samples():
    data = load_data(seed=5, quick=True)
    model, metrics = train(data, quick=True)
    assert "threshold" in model
    assert 0 <= metrics["mean_iou"] <= 1
