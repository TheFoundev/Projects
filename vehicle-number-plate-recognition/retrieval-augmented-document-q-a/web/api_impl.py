"""The API of the question answering service.

The retrieval of the project really runs: the handbook is turned into a TF-IDF
matrix, the passage that matches the question best is looked up, and the
answer is the sentence of that passage which is closest to the question. The
hit rate and the overlap rate are the measures of the project.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.data import load_data  # noqa: E402
from src.model import answer, train  # noqa: E402

#: The corpus and the metrics of the run, kept between the calls.
_CACHE: dict[int, tuple] = {}


def _state(seed: int = 42):
    """The corpus, the questions and the metrics of the run."""
    if seed not in _CACHE:
        data = load_data(seed=seed)
        model, metrics = train(data)
        _CACHE[seed] = (data, model, metrics)
    return _CACHE[seed]


def _number(payload, key: str, default: int) -> int:
    """One number of the request; a query string arrives as a list."""
    value = (payload or {}).get(key, default)
    if isinstance(value, (list, tuple)):
        value = value[0] if value else default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _overlap(reference: str, answer_text: str) -> float:
    """The share of the words of the reference that the answer keeps."""
    reference_words = set(re.findall(r"[a-z0-9]+", reference.lower()))
    answer_words = set(re.findall(r"[a-z0-9]+", answer_text.lower()))
    return len(reference_words & answer_words) / max(1, len(reference_words))


def summary():
    data, _, metrics = _state()
    rows = []
    for question, reference, source in data["questions"]:
        result = answer(question, data["documents"])
        rows.append({
            "question": question,
            "answer": result["answer"],
            "source": result["source"],
            "hit": int(result["source"] == source),
            "overlap": round(_overlap(reference, result["answer"]), 4),
        })

    return {
        "stats": {
            "hit_rate": metrics["retrieval_hit_rate"],
            "overlap_rate": metrics["answer_overlap_rate"],
            "questions": metrics["questions"],
            "documents": metrics["documents"],
        },
        "series": [{"label": row["question"][:26], "value": row["overlap"]} for row in rows],
        "lists": {
            "questions": rows,
            "documents": [
                {"id": name, "text": text} for name, text in data["documents"]
            ],
        },
    }


def handle(method, path, payload, user):
    if method == "POST" and path == "/api/ask":
        question = str((payload or {}).get("question", "")).strip()
        if not question:
            return 400, {"error": "no question was sent"}
        seed = _number(payload, "seed", 42)
        data, _, _ = _state(seed)
        result = answer(question, data["documents"])
        reference = next((item[1] for item in data["questions"] if item[0] == question), "")
        return 200, {
            "question": question,
            "answer": result["answer"],
            "source": result["source"],
            "score": round(float(result["score"]), 4),
            "overlap": round(_overlap(reference, result["answer"]), 4) if reference else None,
        }

    if method == "POST" and path == "/api/train":
        seed = _number(payload, "seed", 42)
        _CACHE.pop(seed, None)
        state = summary()
        return 200, {"retrained": True, "summary": state}

    return 404, {"error": "not found"}
