"""Tests for the topic modelling."""
from src.data import load_data
from src.model import demo, train


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


def test_every_document_gets_a_topic():
    data = load_data(seed=3, quick=True)
    model, metrics = train(data, quick=True)
    assert len(model["topics"]) == metrics["topics"]
    assert len(model["assignments"]) == len(data["documents"])


def test_the_terms_of_a_topic_are_words():
    data = load_data(seed=3, quick=True)
    model, _ = train(data, quick=True)
    for terms in model["topics"]:
        assert terms
        for term in terms:
            assert isinstance(term, str)
