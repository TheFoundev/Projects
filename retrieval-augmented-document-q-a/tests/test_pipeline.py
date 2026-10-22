"""Tests for the retrieval pipeline."""
from src.data import load_data
from src.model import answer, demo, sentences, train


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


def test_the_text_is_split_into_sentences():
    parts = sentences("One. Two! Three?")
    assert parts == ["One.", "Two!", "Three?"]


def test_the_answer_cites_a_source():
    data = load_data(seed=4, quick=True)
    result = answer(data["questions"][0][0], data["documents"])
    assert result["answer"]
    assert result["source"]


def test_the_source_is_one_of_the_documents():
    data = load_data(seed=4, quick=True)
    result = answer(data["questions"][0][0], data["documents"])
    names = [name for name, _ in data["documents"]]
    assert result["source"] in names


def test_the_hit_rate_is_a_share():
    data = load_data(seed=4, quick=True)
    _, metrics = train(data, quick=True)
    assert 0 <= metrics["retrieval_hit_rate"] <= 1
    assert 0 <= metrics["answer_overlap_rate"] <= 1
    assert metrics["questions"] == len(data["questions"])
