"""Tests for the defect detection."""
import numpy as np

from src.data import load_data, make_patch
from src.model import demo, flatten, reconstruction_scores, train


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


def test_a_clean_patch_and_a_defective_one_are_not_the_same():
    clean, _, clean_label = make_patch(seed=1, size=32, defective=False)
    defective, _, defective_label = make_patch(seed=1, size=32, defective=True)
    assert not np.array_equal(clean, defective)
    assert clean_label == 0
    assert defective_label == 1


def test_the_patches_are_flattened_to_a_vector():
    patch, _, _ = make_patch(seed=1, size=32)
    vector = flatten([patch])
    assert vector.shape[1] == 32 * 32


def test_the_scores_of_a_defective_patch_are_higher():
    data = load_data(seed=2, quick=True)
    model, _ = train(data, quick=True)
    pca = model["pca"] if isinstance(model, dict) else model

    clean, _, _ = make_patch(seed=5, size=32, defective=False)
    defective, _, _ = make_patch(seed=5, size=32, defective=True)

    clean_score = reconstruction_scores(pca, flatten([clean]))[0]
    defective_score = reconstruction_scores(pca, flatten([defective]))[0]
    assert defective_score > clean_score


def test_the_metrics_are_shares():
    data = load_data(seed=4, quick=True)
    _, metrics = train(data, quick=True)
    assert 0 <= metrics["roc_auc"] <= 1
    assert 0 <= metrics["precision"] <= 1
    assert 0 <= metrics["recall"] <= 1
