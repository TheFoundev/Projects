"""Tests for the promptable segmentation."""
import numpy as np
from src.data import load_data, make_sample
from src.model import (
    decode,
    decode_box,
    decode_point,
    encode_image,
    encode_mask,
    evaluate,
    fine_tune,
    iou,
    segment,
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
        assert value is None or isinstance(value, (int, float, str, list))

    demo(data)
    assert capsys.readouterr().out.strip()


def test_seed_is_usable():
    first = load_data(seed=3, quick=True)
    second = load_data(seed=3, quick=True)
    assert first.keys() == second.keys()


def test_a_point_on_an_object_gives_the_object():
    sample = make_sample(seed=2)
    mask = segment(sample["image"], sample["point"])
    assert mask.any()
    assert iou(mask, sample["mask"]) > 0.5


def test_a_point_outside_an_object_gives_an_empty_mask():
    sample = make_sample(seed=2)
    mask = segment(sample["image"], (0, 0))
    assert mask.sum() == 0


def test_a_point_outside_the_image_gives_an_empty_mask():
    sample = make_sample(seed=2)
    mask = segment(sample["image"], (999, 999))
    assert mask.sum() == 0


def test_a_box_gives_the_object_it_points_at():
    sample = make_sample(seed=4)
    embedding = encode_image(sample["image"])
    ys, xs = np.where(sample["mask"])
    left, right = int(xs.min()) - 2, int(xs.max()) + 2
    top, bottom = int(ys.min()) - 2, int(ys.max()) + 2

    mask = decode_box(embedding, (left, top, right, bottom))
    assert iou(mask, sample["mask"]) > 0.5


def test_the_encoder_finds_the_objects():
    sample = make_sample(seed=6)
    embedding = encode_image(sample["image"])
    assert embedding["count"] >= 1
    assert embedding["probability"].max() > 0


def test_the_fine_tuning_improves_the_loss():
    data = load_data(seed=8, quick=True)
    model, metrics = fine_tune(data, quick=True)

    assert metrics["history"][0] >= metrics["history"][-1]
    assert metrics["loss"] <= metrics["history"][0]
    assert "threshold" in model and "bias" in model


def test_the_evaluation_reports_the_mean_and_the_hits():
    data = load_data(seed=10, quick=True)
    mean_iou, success = evaluate(data["samples"], 110)
    assert 0 <= mean_iou <= 1
    assert 0 <= success <= 1


def test_the_mask_can_be_encoded():
    sample = make_sample(seed=12)
    mask = segment(sample["image"], sample["point"])
    encoded = encode_mask(mask)

    assert encoded["size"] == list(sample["image"].shape)
    assert sum(encoded["counts"]) == int(mask.size)

    # The encoding can be read back into the same mask.
    pixels = []
    value = encoded["first"]
    for count in encoded["counts"]:
        pixels.extend([value] * count)
        value = not value
    assert np.array_equal(np.array(pixels, dtype=bool).reshape(mask.shape), mask)


def test_a_prompt_that_is_nothing_gives_an_empty_mask():
    sample = make_sample(seed=14)
    embedding = encode_image(sample["image"])
    mask = decode(embedding, {})
    assert mask.sum() == 0
