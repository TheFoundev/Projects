"""Tests for the entity recognition."""
from src.data import load_data
from src.model import demo, spans, token_features, train


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


def test_the_spans_of_a_labeled_sentence():
    tokens = ["Ada", "Lovelace", "wrote", "in", "London"]
    labels = ["PER", "PER", "O", "O", "LOC"]
    found = spans(tokens, labels)
    assert ("PER", "Ada Lovelace") in found
    assert ("LOC", "London") in found


def test_the_spans_of_a_bio_labeled_sentence():
    """A token marked as a continuation belongs to the entity before it."""
    tokens = ["Ada", "Lovelace", "wrote"]
    labels = ["B-PER", "I-PER", "O"]
    found = spans(tokens, labels)
    assert ("PER", "Ada Lovelace") in found, found
