"""A logistic regression over the text of a resume, with the questions for the
interview drafted from what the resume says."""
import re
import sqlite3
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score

from src.data import SKILLS, parse_resume

#: The questions that are asked when the resume says nothing about a skill.
GENERIC_QUESTIONS = [
    "Tell me about a project you finished on your own. What was hard about it?",
    "How do you decide what to build first when everything feels urgent?",
    "Describe a time you had to hand something over to someone else. What went wrong?",
]

#: The question that goes with every skill, so the interviewer can go deeper.
SKILL_QUESTIONS = {
    "python": "Where did you use Python in production, and what did you have to learn the hard way?",
    "sql": "How do you tell the difference between a slow SQL query and a wrong one?",
    "rest": "How do you decide what belongs in a REST answer and what does not?",
    "testing": "What do you test, and what do you deliberately not test?",
    "docker": "What broke the first time you put this in Docker?",
    "flask": "How do you keep a Flask service from becoming a pile of routes?",
    "pandas": "What did the data look like before you cleaned it with pandas?",
    "git": "How do you and your team handle a Git branch that is two weeks old?",
    "linux": "What is the first thing you check on Linux when a service is slow?",
    "react": "How do you decide what a React screen should show before it loads?",
    "typescript": "What does TypeScript catch for you that a test would not?",
}


def resume_features(resume):
    """The features of a resume.

    The facts come from the text of the resume, so the parser is used and not
    the fields the generator filled in.
    """
    parsed = parse_resume(resume["text"])
    text = resume["text"].lower()
    found = [skill for skill in SKILLS if skill in text]

    return {
        "text": resume["text"],
        "years": parsed["years"],
        "projects": parsed["projects"],
        "education": parsed["education"],
        "skills": found,
    }


def draft_interview_questions(resume, job_description=""):
    """The questions for the interview, drafted from the resume.

    Every skill the resume mentions gets a question of its own, and the
    questions of the job are added when the resume says nothing about them.
    """
    parsed = parse_resume(resume["text"])
    questions = []

    for skill in parsed["skills"]:
        question = SKILL_QUESTIONS.get(skill)
        if question:
            questions.append(question)

    if parsed["projects"] == 0:
        questions.append("You have not listed a project. What have you built so far?")

    if parsed["years"] < 2:
        questions.append("How do you keep up with a codebase that is bigger than you are?")

    # Every word of the job the resume says nothing about gets a question.
    wanted = [
        word
        for word in re.findall(r"[a-zA-Z][a-zA-Z\-]{3,}", job_description.lower())
        if word not in parsed["skills"]
    ]
    for word in wanted:
        if len(questions) >= 5:
            break
        questions.append(f"The job needs {word}. What have you done with it?")

    for question in GENERIC_QUESTIONS:
        if len(questions) >= 5:
            break
        questions.append(question)

    return questions[:6]


def _matrix(rows, vectorizer):
    """The matrix of the features, the text and the numbers together."""
    text = vectorizer.transform([row["text"] for row in rows]).toarray()
    numbers = np.array(
        [[row["years"], row["projects"], len(row["skills"])] for row in rows],
        dtype=float,
    )
    return np.hstack([text, numbers])


def train(data, quick=False, db_path="artifacts/candidates.db"):
    """Fit the classifier and store the candidates."""
    train_rows = [resume_features(resume) for resume in data["train"]]
    test_rows = [resume_features(resume) for resume in data["test"]]

    vectorizer = TfidfVectorizer(stop_words="english", max_features=120)
    vectorizer.fit([row["text"] for row in train_rows])

    augmented_train = _matrix(train_rows, vectorizer)
    augmented_test = _matrix(test_rows, vectorizer)

    labels = np.array([resume["label"] for resume in data["train"]])

    model = LogisticRegression(max_iter=400)
    model.fit(augmented_train, labels)
    prediction = model.predict(augmented_test)
    truth = np.array([resume["label"] for resume in data["test"]])

    target = Path(db_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(target)
    connection.execute(
        "CREATE TABLE IF NOT EXISTS candidates (name TEXT, years INT, skills TEXT, score REAL, shortlisted INT)"
    )
    connection.execute("DELETE FROM candidates")
    probabilities = model.predict_proba(augmented_test)[:, 1]
    for resume, score, shortlisted in zip(data["test"], probabilities, prediction):
        connection.execute(
            "INSERT INTO candidates VALUES (?, ?, ?, ?, ?)",
            (resume["name"], resume["years"], ",".join(resume["skills"]), float(score), int(shortlisted)),
        )
    connection.commit()
    connection.close()

    return {"vectorizer": vectorizer, "classifier": model}, {
        "precision": round(float(precision_score(truth, prediction, zero_division=0)), 4),
        "recall": round(float(recall_score(truth, prediction, zero_division=0)), 4),
        "shortlisted": int(prediction.sum()),
        "candidates": int(len(data["test"])),
    }


def rank_candidates(model, data):
    """The candidates of the test set, the best first."""
    rows = [resume_features(resume) for resume in data["test"]]
    matrix = _matrix(rows, model["vectorizer"])
    scores = model["classifier"].predict_proba(matrix)[:, 1]
    order = np.argsort(scores)[::-1]
    return [(data["test"][int(index)], float(scores[index])) for index in order]


def demo(data):
    model, metrics = train(data, quick=True)
    ranked = rank_candidates(model, data)
    print("Ranked candidates:")
    for resume, score in ranked[:4]:
        print(f"  {resume['name']:14s} score={score:.2f} skills={','.join(resume['skills'][:4])}")
    print(f"Shortlist precision: {metrics['precision']:.2f}, recall: {metrics['recall']:.2f}")

    print("\nQuestions for the interview of the first candidate:")
    for question in draft_interview_questions(ranked[0][0], data["job_description"]):
        print(f"  - {question}")
