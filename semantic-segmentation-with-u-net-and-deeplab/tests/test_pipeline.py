"""Tests for the segmentation."""
import numpy as np

from src.data import load_data
from src.model import build_unet, demo, dice_score, train


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


def test_the_dice_of_a_mask_with_itself_is_one():
    mask = np.zeros((10, 10), dtype=bool)
    mask[2:6, 2:6] = True
    assert dice_score(mask, mask) == 1.0


def test_the_dice_of_two_masks_that_do_not_touch_is_zero():
    first = np.zeros((10, 10), dtype=bool)
    second = np.zeros((10, 10), dtype=bool)
    first[0:2, 0:2] = True
    second[8:10, 8:10] = True
    assert dice_score(first, second) == 0.0


def test_the_network_makes_a_mask_of_the_right_size():
    model = build_unet(size=32)
    output = model.predict(np.zeros((1, 32, 32, 1), dtype="float32"), verbose=0)
    assert output.shape == (1, 32, 32, 1)
