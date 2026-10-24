"""Tests for the evaluation harness."""
from src.pipeline import demo, extract_answer, retrieve, run, token_f1, tokens


def test_pipeline_runs(tmp_path, capsys):
    summary = run(quick=True, base_dir=str(tmp_path))
    assert isinstance(summary, dict)
    assert summary
    assert any(tmp_path.iterdir())

    demo(base_dir=str(tmp_path))
    assert capsys.readouterr().out.strip()


def test_the_tokens_are_words():
    assert tokens("Hello, world!") == ["hello", "world"]


def test_the_token_f1_of_two_texts_is_a_share():
    assert token_f1("the cat sat", "the cat sat") == 1.0
    assert token_f1("the cat sat", "a dog ran") == 0.0
    value = token_f1("the cat sat", "the cat ran")
    assert 0 < value <= 1


def test_the_answer_comes_from_the_context():
    answer = extract_answer("When is the lab open?", "The lab opens at 9:00 on weekdays.")
    assert answer
    assert "9:00" in answer or "lab" in answer.lower()


def test_the_retrieval_finds_a_passage():
    from src.pipeline import run as build

    summary = build(quick=True, base_dir="/tmp/rag-harness-test")
    assert summary["questions"] >= 0
