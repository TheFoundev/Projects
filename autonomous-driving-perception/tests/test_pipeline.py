"""Tests for the perception baseline."""
import numpy as np

from src.data import load_data, make_scene
from src.model import (
    box_iou,
    detect_vehicles,
    evaluate,
    lane_iou,
    match_detections,
    split_scenes,
    train,
    demo,
)


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


# ---------------------------------------------------------------------------
# The metrics
# ---------------------------------------------------------------------------

def test_the_lane_iou_of_a_mask_with_itself_is_one():
    mask = np.zeros((10, 10), dtype=bool)
    mask[2:6, 2:6] = True
    assert lane_iou(mask, mask) == 1.0


def test_the_lane_iou_of_two_masks_that_do_not_touch_is_zero():
    first = np.zeros((10, 10), dtype=bool)
    second = np.zeros((10, 10), dtype=bool)
    first[0:2, 0:2] = True
    second[8:10, 8:10] = True
    assert lane_iou(first, second) == 0.0


def test_the_box_iou_of_a_box_with_itself_is_one():
    assert box_iou([0, 0, 10, 10], [0, 0, 10, 10]) == 1.0
    assert box_iou([0, 0, 10, 10], [20, 20, 30, 30]) == 0.0


def test_a_detection_is_matched_to_the_truth_it_overlaps():
    detections = [[0, 0, 10, 10], [50, 50, 60, 60]]
    truths = [[1, 1, 11, 11]]
    matched = match_detections(detections, truths)

    assert matched["true_positive"] == 1
    assert matched["false_positive"] == 1
    assert matched["false_negative"] == 0


def test_a_detection_is_used_at_most_once():
    detections = [[0, 0, 10, 10]]
    truths = [[0, 0, 10, 10], [0, 0, 10, 10]]
    matched = match_detections(detections, truths)

    assert matched["true_positive"] == 1
    assert matched["false_negative"] == 1


# ---------------------------------------------------------------------------
# The detector
# ---------------------------------------------------------------------------

def test_the_detector_finds_the_vehicles_of_a_scene():
    scene = make_scene(seed=2, size=96)
    boxes = detect_vehicles(scene["image"])

    assert len(boxes) == len(scene["boxes"])
    for truth, found in zip(scene["boxes"], sorted(boxes)):
        assert box_iou(truth, found) > 0.5


def test_the_lane_pixels_are_not_reported_as_vehicles():
    """The lane edges are bright as well, but they are long and thin."""
    scene = make_scene(seed=3, size=96)
    boxes = detect_vehicles(scene["image"])

    for box in boxes:
        width = box[2] - box[0]
        height = box[3] - box[1]
        assert width / height <= 5
        assert height / width <= 5


def test_an_empty_scene_has_no_vehicles():
    empty = np.zeros((40, 40))
    assert detect_vehicles(empty) == []


# ---------------------------------------------------------------------------
# The training
# ---------------------------------------------------------------------------

def test_the_threshold_is_fitted_on_one_part_and_measured_on_the_other():
    data = load_data(seed=4, quick=False)
    tuning, testing = split_scenes(data)

    assert tuning
    assert testing
    assert len(tuning) + len(testing) == len(data["scenes"])


def test_the_metrics_are_measured_on_the_held_out_scenes():
    data = load_data(seed=4, quick=False)
    model, metrics = train(data, quick=False)

    assert metrics["test_scenes"] > 0
    assert metrics["tuning_scenes"] > 0
    assert 0 <= metrics["lane_iou"] <= 1
    assert 0 <= metrics["vehicle_precision"] <= 1
    assert 0 <= metrics["vehicle_recall"] <= 1


def test_the_evaluation_reports_the_number_of_scenes():
    data = load_data(seed=4, quick=True)
    metrics = evaluate(data["scenes"])
    assert metrics["scenes"] == len(data["scenes"])
