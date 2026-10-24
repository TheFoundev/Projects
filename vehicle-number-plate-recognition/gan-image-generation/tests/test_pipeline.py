"""Tests for the generative adversarial network."""
import numpy as np

from src.data import load_data
from src.model import build_discriminator, build_generator, demo, train


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


def test_the_generator_makes_an_image_of_the_right_size():
    generator = build_generator(latent=8)
    noise = np.random.default_rng(0).normal(0, 1, (4, 8)).astype("float32")
    images = generator(noise, training=False)
    images = np.asarray(images)
    assert images.shape == (4, 16, 16, 1)
    assert float(images.min()) >= -1.0
    assert float(images.max()) <= 1.0


def test_the_discriminator_says_how_real_an_image_is():
    discriminator = build_discriminator(size=16)
    images = np.zeros((2, 16, 16, 1), dtype="float32")
    scores = discriminator(images, training=False)
    assert tuple(np.asarray(scores).shape) == (2, 1)


def test_the_losses_are_reported():
    data = load_data(seed=4, quick=True)
    _, metrics = train(data, quick=True)
    assert "generator_loss" in metrics
    assert "discriminator_loss" in metrics
