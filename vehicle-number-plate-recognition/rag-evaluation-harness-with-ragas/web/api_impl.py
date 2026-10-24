"""The API of the evaluation harness.

The retrieval and the answer extraction of the project really run: the
questions are answered with a TF-IDF retrieval over the contexts, the answer is
a sentence of the retrieved context, and the hit rate, the token F1 and the
faithfulness are the measures the project computes and writes to
artifacts/evaluation.json.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402

from src.pipeline import (  # noqa: E402
    CONTEXTS,
    QA,
    extract_answer,
    retrieve,
    run,
    token_f1,
)

#: The directory the pipeline writes to.
BASE = ROOT / "artifacts"


def _number(payload, key: str, default: int) -> int:
    """One number of the request; a query string arrives as a list."""
    value = (payload or {}).get(key, default)
    if isinstance(value, (list, tuple)):
        value = value[0] if value else default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _report() -> dict:
    """The evaluation report the pipeline wrote."""
    path = BASE / "evaluation.json"
    if not path.exists():
        return {"examples": []}
    return json.loads(path.read_text(encoding="utf-8"))


def summary():
    result = run(quick=False, base_dir=str(BASE))
    report = _report()
    rows = report.get("examples", [])

    return {
        "stats": {
            "questions": result["questions"],
            "hit_rate": result["retrieval_hit_rate"],
            "answer_f1": result["answer_f1"],
            "faithfulness": result["faithfulness"],
        },
        "series": [{"label": row["question"][:26], "value": row["f1"]} for row in rows],
        "lists": {
            "examples": [
                {"question": row["question"], "answer": row["answer"],
                 "f1": row["f1"], "faithfulness": row["faithfulness"],
                 "hit": row["retrieval_hit"]}
                for row in rows
            ],
            "corpus": [
                {"id": index + 1, "context": context[:70]}
                for index, context in enumerate(CONTEXTS)
            ],
        },
    }


def handle(method, path, payload, user):
    if method == "POST" and path == "/api/ask":
        question = str((payload or {}).get("question", "")).strip()
        if not question:
            return 400, {"error": "no question was sent"}
        vectorizer = TfidfVectorizer(stop_words="english")
        matrix = vectorizer.fit_transform(CONTEXTS)
        index, context = retrieve(question, vectorizer, matrix, CONTEXTS)
        answer = extract_answer(question, context)

        # The reference answer of the set, when the question is one of them.
        reference = next((item[1] for item in QA if item[0] == question), "")
        expected = next((item[2] for item in QA if item[0] == question), None)
        return 200, {
            "question": question,
            "answer": answer,
            "context": context,
            "retrieved_index": index,
            "retrieval_hit": None if expected is None else int(index == expected),
            "f1": round(token_f1(answer, reference), 4) if reference else None,
        }

    if method == "POST" and path == "/api/run":
        quick = bool((payload or {}).get("quick", False))
        result = run(quick=quick, base_dir=str(BASE))
        return 200, {"run": result, "summary": summary()}

    return 404, {"error": "not found"}
