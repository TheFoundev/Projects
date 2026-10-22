"""Retrieval, answer extraction and evaluation metrics."""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

CONTEXTS = [
    "Students reserve a study room through the library portal. Rooms can be booked for two hours at a time.",
    "The bike share programme has twelve stations near campus. A student card unlocks a bike for thirty minutes.",
    "The counselling office is open on weekdays from nine until five. Appointments can be booked online.",
    "Laptops can be borrowed for one day from the help desk. A student card and a signed form are required.",
    "The cafeteria serves breakfast from seven until ten. Lunch is available between eleven and two.",
    "The software lab provides Python and R on every machine. Users should bring their own storage device.",
    "A lost student card should be reported to security immediately. A replacement costs fifteen dollars.",
    "The writing centre reviews drafts by appointment. Sessions last twenty-five minutes and are free.",
    "The gym is open until ten on weekdays and until eight on weekends. Lockers require a small deposit.",
    "Printing credit can be topped up at the library desk. Each page costs five cents.",
]

QA = [
    ("How do students reserve a study room?", "Students reserve a study room through the library portal.", 0),
    ("How long can a bike be unlocked?", "A student card unlocks a bike for thirty minutes.", 1),
    ("When is the counselling office open?", "The counselling office is open on weekdays from nine until five.", 2),
    ("What is needed to borrow a laptop?", "A student card and a signed form are required.", 3),
    ("When is lunch served?", "Lunch is available between eleven and two.", 4),
    ("What software is installed in the lab?", "The software lab provides Python and R on every machine.", 5),
    ("What should I do if I lose my student card?", "A lost student card should be reported to security immediately.", 6),
    ("How long is a writing centre session?", "Sessions last twenty-five minutes and are free.", 7),
    ("When does the gym close on weekends?", "The gym is open until ten on weekdays and until eight on weekends.", 8),
    ("How much does printing cost per page?", "Each page costs five cents.", 9),
]


def tokens(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def token_f1(prediction, reference):
    predicted = tokens(prediction)
    expected = tokens(reference)
    if not predicted or not expected:
        return 0.0
    overlap = 0
    remaining = list(expected)
    for word in predicted:
        if word in remaining:
            remaining.remove(word)
            overlap += 1
    if overlap == 0:
        return 0.0
    precision = overlap / len(predicted)
    recall = overlap / len(expected)
    return 2 * precision * recall / (precision + recall)


def retrieve(question, vectorizer, matrix, contexts):
    scores = (vectorizer.transform([question]) @ matrix.T).toarray()[0]
    index = int(np.argmax(scores))
    return index, contexts[index]


def extract_answer(question, context):
    question_words = set(tokens(question))
    sentences = [part.strip() for part in context.split(".") if part.strip()]
    best = max(sentences, key=lambda sentence: len(question_words & set(tokens(sentence))))
    return best + "."


def run(quick=False, base_dir="artifacts"):
    base = Path(base_dir)
    base.mkdir(parents=True, exist_ok=True)
    examples = QA[:6] if quick else QA
    contexts = CONTEXTS[:6] if quick else CONTEXTS

    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(contexts)

    results = []
    for question, reference, expected_index in examples:
        index, context = retrieve(question, vectorizer, matrix, contexts)
        prediction = extract_answer(question, context)
        predicted_tokens = set(tokens(prediction))
        context_tokens = set(tokens(context))
        results.append({
            "question": question,
            "retrieved_index": index,
            "retrieval_hit": int(index == expected_index),
            "answer": prediction,
            "reference": reference,
            "f1": round(token_f1(prediction, reference), 4),
            "faithfulness": round(len(predicted_tokens & context_tokens) / max(1, len(predicted_tokens)), 4),
        })

    report = {
        "examples": results,
        "retrieval_hit_rate": round(float(np.mean([row["retrieval_hit"] for row in results])), 4),
        "answer_f1": round(float(np.mean([row["f1"] for row in results])), 4),
        "faithfulness": round(float(np.mean([row["faithfulness"] for row in results])), 4),
    }
    (base / "evaluation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    pd.DataFrame(results).to_csv(base / "evaluation.csv", index=False)
    return {
        "questions": len(results),
        "retrieval_hit_rate": report["retrieval_hit_rate"],
        "answer_f1": report["answer_f1"],
        "faithfulness": report["faithfulness"],
        "report": str(base / "evaluation.json"),
    }


def demo(base_dir="artifacts"):
    summary = run(quick=True, base_dir=base_dir)
    report = json.loads((Path(base_dir) / "evaluation.json").read_text())
    for row in report["examples"]:
        print(f"Q: {row['question']}")
        print(f"  answer: {row['answer']}")
        print(f"  retrieval_hit={row['retrieval_hit']} f1={row['f1']:.2f} faithfulness={row['faithfulness']:.2f}")
    print(f"Hit rate {summary['retrieval_hit_rate']:.2f}, F1 {summary['answer_f1']:.2f}, faithfulness {summary['faithfulness']:.2f}")
