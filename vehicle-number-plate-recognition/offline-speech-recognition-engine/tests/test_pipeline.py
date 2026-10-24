"""Tests for the offline speech recognition."""
import numpy as np

from src.data import load_data
from src.model import dtw_distance, train, demo


def test_the_distance_of_a_sequence_with_itself_is_zero():
    sequence = np.array([[0.0, 1.0], [1.0, 2.0], [2.0, 3.0]])
    assert dtw_distance(sequence, sequence) == 0.0


def test_the_distance_of_two_empty_sequences_is_not_a_number():
    assert dtw_distance(np.zeros((0, 2)), np.zeros((0, 2))) == float("inf")


def test_the_distance_grows_with_the_difference():
    first = np.array([[0.0, 0.0], [1.0, 1.0]])
    second = np.array([[0.0, 0.0], [1.0, 1.0]])
    third = np.array([[5.0, 5.0], [6.0, 6.0]])
    assert dtw_distance(first, third) > dtw_distance(first, second)


def test_the_band_does_not_change_the_distance_of_a_short_sequence():
    first = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]])
    second = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]])
    assert dtw_distance(first, second, band=3) == dtw_distance(first, second)


def test_the_pipeline_runs(capsys):
    data = load_data(seed=1, quick=True)
    model, metrics = train(data, quick=True)
    assert model is not None
    assert isinstance(metrics, dict) and metrics
    demo(data)
    assert capsys.readouterr().out.strip()
