"""Tests for the upscaler."""
import numpy as np

from src.data import downsample, load_data, make_image
from src.model import demo, evaluate, psnr, train, upscale


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


def test_the_image_is_downsampled_by_the_factor():
    image = make_image(seed=1, size=64)
    low = downsample(image, factor=4)
    assert low.shape[:2] == (16, 16)


def test_the_upscaler_makes_a_bigger_image():
    image = make_image(seed=1, size=64)
    low = downsample(image, factor=4)
    high = upscale(low, radius=1.2, percent=140, threshold=2)
    assert high.shape[:2] == (64, 64)


def test_the_psnr_of_an_image_with_itself_is_big():
    image = make_image(seed=1, size=32)
    assert psnr(image, image) > 50


def test_the_evaluation_reports_a_psnr():
    data = load_data(seed=4, quick=True)
    score, error = evaluate(data["pairs"])
    assert score > 0
    assert error >= 0
