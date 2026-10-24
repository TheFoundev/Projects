"""Tests for the screening pipeline, the parser and the questions."""
import sqlite3

import pytest

from src.data import load_data, make_resume, parse_resume
from src.model import draft_interview_questions, rank_candidates, train, demo
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
        assert value is None or isinstance(value, (int, float, str))

    demo(data)
    assert capsys.readouterr().out.strip()


def test_seed_is_usable():
    first = load_data(seed=3, quick=True)
    second = load_data(seed=3, quick=True)
    assert first.keys() == second.keys()


# ---------------------------------------------------------------------------
# The parser
# ---------------------------------------------------------------------------

def test_the_parser_reads_the_facts_of_a_resume():
    resume = make_resume(0, seed=1)
    parsed = parse_resume(resume["text"])

    assert parsed["years"] == resume["years"]
    assert parsed["projects"] == resume["projects"]
    assert parsed["education"] == resume["education"]
    # The parser can only find the skills the text mentions.
    assert set(parsed["skills"]).issubset(set(resume["skills"]))


def test_the_parser_of_a_text_without_a_fact_gives_zero():
    parsed = parse_resume("A short note about nothing in particular.")
    assert parsed["years"] == 0
    assert parsed["projects"] == 0
    assert parsed["skills"] == []


# ---------------------------------------------------------------------------
# The label
# ---------------------------------------------------------------------------

def test_the_label_is_not_a_function_of_the_skills():
    """The label may not be computed from the skills the model reads.

    The same skills with a different work history can give a different label,
    so the skills alone do not decide it.
    """
    from src.data import make_resume as build

    same_skills = ["python", "sql", "testing"]
    labels = {
        build(index, seed=3, skills=same_skills)["label"]
        for index in range(40)
    }
    assert len(labels) == 2, f"the same skills can give both labels, got {labels}"


# ---------------------------------------------------------------------------
# The training
# ---------------------------------------------------------------------------

def test_the_metrics_are_reported(tmp_path):
    data = load_data(seed=5, quick=True)
    _, metrics = train(data, quick=True, db_path=str(tmp_path / "candidates.db"))

    assert 0 <= metrics["precision"] <= 1
    assert 0 <= metrics["recall"] <= 1
    assert metrics["candidates"] == len(data["test"])
    assert metrics["shortlisted"] == int(metrics["shortlisted"])


def test_the_candidates_are_stored(tmp_path):
    data = load_data(seed=5, quick=True)
    path = tmp_path / "candidates.db"
    train(data, quick=True, db_path=str(path))

    connection = sqlite3.connect(path)
    rows = connection.execute("SELECT name, years, skills, score, shortlisted FROM candidates").fetchall()
    connection.close()

    assert len(rows) == len(data["test"])
    assert all(0 <= row[3] <= 1 for row in rows)
    assert all(row[4] in (0, 1) for row in rows)


def test_the_candidates_are_ranked(tmp_path):
    data = load_data(seed=5, quick=True)
    model, _ = train(data, quick=True, db_path=str(tmp_path / "candidates.db"))
    ranked = rank_candidates(model, data)

    assert len(ranked) == len(data["test"])
    scores = [score for _, score in ranked]
    assert scores == sorted(scores, reverse=True)


# ---------------------------------------------------------------------------
# The questions
# ---------------------------------------------------------------------------

def test_the_questions_are_drafted_from_the_resume():
    resume = make_resume(0, seed=2)
    questions = draft_interview_questions(resume, "We need Python and SQL.")

    assert questions
    assert len(questions) <= 6
    assert all(isinstance(question, str) and question.endswith("?") for question in questions)


def test_a_skill_of_the_resume_gets_a_question():
    resume = {
        "name": "Candidate",
        "text": "Candidate has 5 years of experience and a master degree. "
                "Recent work used python, sql and docker. "
                "Completed 3 portfolio projects and collaborated in small teams.",
    }
    questions = draft_interview_questions(resume, "")
    joined = " ".join(questions).lower()

    assert "python" in joined
    assert "docker" in joined


def test_a_skill_of_the_job_that_is_missing_gets_a_question():
    resume = {
        "name": "Candidate",
        "text": "Candidate has 5 years of experience and a master degree. "
                "Recent work used python. Completed 3 portfolio projects.",
    }
    questions = draft_interview_questions(resume, "We need Kubernetes and Terraform.")
    assert any("kubernetes" in question.lower() for question in questions)
    assert any("terraform" in question.lower() for question in questions)


def test_a_resume_without_projects_gets_a_question():
    resume = make_resume(0, seed=2)
    resume["text"] = "Candidate 00 has 1 years of experience and a diploma degree."
    questions = draft_interview_questions(resume, "")
    assert any("project" in question.lower() for question in questions)


# ---------------------------------------------------------------------------
# The page and the web layer
# ---------------------------------------------------------------------------

def test_the_page_lists_the_candidates():
    response = flask_app.test_client().get("/candidates")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Candidate" in body
    assert "precision" in body


def test_the_site_is_served():
    client = flask_app.test_client()
    for route in ("/", "/console.html", "/assets/theme.css"):
        assert client.get(route).status_code == 200


def test_the_summary_answers_with_the_real_numbers():
    answer = flask_app.test_client().get("/api/summary").get_json()

    assert answer["stats"]["candidates"] == len(answer["lists"]["candidates"])
    assert 0 <= answer["stats"]["precision"] <= 1
    assert 0 <= answer["stats"]["recall"] <= 1
    assert answer["lists"]["questions"]


def test_the_candidates_are_ranked_in_the_api():
    answer = flask_app.test_client().get("/api/candidates").get_json()
    scores = [row["score"] for row in answer["candidates"]]

    assert scores == sorted(scores, reverse=True)
