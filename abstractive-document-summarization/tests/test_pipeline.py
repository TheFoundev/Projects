"""Tests for the summarizer, the scoring and the page."""
import pytest

from src.data import load_data, split_sentences
from src.model import LENGTHS, rouge_l, score_length, search_length, summarize, train, demo
from app import app as flask_app


def test_pipeline_runs(capsys):
    data = load_data(seed=1, quick=True)
    assert data is not None

    model, metrics = train(data, quick=True)
    assert model is not None
    assert isinstance(metrics, dict) and metrics

    for value in metrics.values():
        if isinstance(value, bool):
            continue
        assert value is None or isinstance(value, (int, float, str, list, dict))

    demo(data)
    assert capsys.readouterr().out.strip()


def test_seed_is_usable():
    first = load_data(seed=3, quick=True)
    second = load_data(seed=3, quick=True)
    assert first.keys() == second.keys()


def test_the_summary_keeps_the_number_of_sentences():
    data = load_data(seed=1, quick=False)
    document = data["documents"][0]
    sentences = split_sentences(document)

    summary = summarize(document, max_sentences=2)
    assert len(split_sentences(summary)) == 2
    assert len(sentences) > 2


def test_a_short_document_is_returned_as_it_is():
    assert summarize("One sentence only.", max_sentences=2) == "One sentence only."


def test_the_summary_is_made_of_the_sentences_of_the_document():
    data = load_data(seed=2, quick=False)
    document = data["documents"][1]
    sentences = split_sentences(document)
    summary = summarize(document, max_sentences=3)
    for sentence in split_sentences(summary):
        assert sentence in sentences


def test_the_rouge_of_a_text_with_itself_is_one():
    text = "the quick brown fox jumps over the lazy dog"
    assert rouge_l(text, text) == pytest.approx(1.0)


def test_the_rouge_of_two_unrelated_texts_is_zero():
    assert rouge_l("alpha beta", "gamma delta") == 0.0


def test_the_rouge_grows_with_the_overlap():
    reference = "the city opened a protected bike lane on king street"
    partial = "the city opened a protected bike lane"
    full = reference
    assert rouge_l(reference, partial) < rouge_l(reference, full)


def test_the_rouge_of_an_empty_text_is_zero():
    assert rouge_l("", "something") == 0.0
    assert rouge_l("something", "") == 0.0


def test_the_length_is_searched_and_the_best_one_is_kept():
    data = load_data(seed=5, quick=False)
    model, metrics = train(data, quick=False)

    assert model["max_sentences"] in LENGTHS
    assert set(model["scores_by_length"]) == set(LENGTHS)
    assert metrics["rouge_l"] == max(model["scores_by_length"].values())


def test_the_search_reports_the_score_of_every_length():
    data = load_data(seed=5, quick=False)
    best_length, best_score, results = search_length(data, LENGTHS)

    assert best_length in LENGTHS
    assert best_score == max(results.values())
    assert all(0 <= score <= 1 for score in results.values())


def test_the_score_of_a_length_is_the_mean_of_the_corpus():
    data = load_data(seed=6, quick=True)
    score = score_length(data, 2)
    expected = sum(
        rouge_l(reference, summarize(document, max_sentences=2))
        for document, reference in zip(data["documents"], data["references"])
    ) / len(data["documents"])
    assert score == pytest.approx(expected)


def test_the_page_answers_with_a_summary():
    client = flask_app.test_client()
    response = client.post("/summarize", data={"text": "One. Two. Three. Four."})
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Summary" in body


def test_the_page_without_a_text_has_no_summary():
    client = flask_app.test_client()
    response = client.get("/summarize")
    assert response.status_code == 200
    assert "Summary" not in response.get_data(as_text=True)


# ---------------------------------------------------------------------------
# The web layer
# ---------------------------------------------------------------------------

def test_the_site_is_served():
    client = flask_app.test_client()
    for route in ("/", "/console.html", "/assets/theme.css"):
        assert client.get(route).status_code == 200


def test_the_summary_answers_with_the_real_numbers():
    client = flask_app.test_client()
    answer = client.get("/api/summary").get_json()

    assert answer["stats"]["documents"] == 8
    assert 0 <= answer["stats"]["rouge_l"] <= 1
    assert answer["stats"]["max_sentences"] in LENGTHS
    assert len(answer["lists"]["documents"]) == 8


def test_the_api_summarizes_a_document():
    client = flask_app.test_client()
    answer = client.post("/api/summarize", json={"text": "One. Two. Three. Four."}).get_json()

    assert answer["summary"]
    assert answer["sentences"] in LENGTHS
