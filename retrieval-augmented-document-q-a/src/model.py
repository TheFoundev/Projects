"""Retrieval followed by sentence-level answer extraction."""
import re

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def sentences(text):
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]


def answer(question, documents, top_k=2):
    texts = [text for _, text in documents]
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(texts + [question])
    scores = cosine_similarity(matrix[-1], matrix[:-1]).ravel()
    order = np.argsort(scores)[::-1][:top_k]

    candidates = []
    for index in order:
        doc_id, _ = documents[index]
        for sentence in sentences(texts[index]):
            candidates.append((doc_id, sentence, float(scores[index])))

    if not candidates:
        return {"answer": "", "source": "", "score": 0.0}

    question_vector = vectorizer.transform([question])
    sentence_matrix = vectorizer.transform([item[1] for item in candidates])
    sentence_scores = cosine_similarity(question_vector, sentence_matrix).ravel()
    best = int(np.argmax(sentence_scores))
    doc_id, sentence, retrieval_score = candidates[best]
    return {
        "answer": sentence,
        "source": doc_id,
        "score": float(retrieval_score + sentence_scores[best]),
    }


def train(data, quick=False):
    hits = 0
    phrase_hits = 0
    for question, reference, source in data["questions"]:
        result = answer(question, data["documents"])
        hits += int(result["source"] == source)
        reference_words = set(re.findall(r"[a-z0-9]+", reference.lower()))
        answer_words = set(re.findall(r"[a-z0-9]+", result["answer"].lower()))
        phrase_hits += int(len(reference_words & answer_words) / max(1, len(reference_words)) >= 0.6)
    count = len(data["questions"])
    return {"retriever": "tfidf", "top_k": 2}, {
        "retrieval_hit_rate": round(hits / count, 4),
        "answer_overlap_rate": round(phrase_hits / count, 4),
        "questions": count,
        "documents": len(data["documents"]),
    }


def demo(data):
    print("Question:", data["questions"][0][0])
    result = answer(data["questions"][0][0], data["documents"])
    print("Answer:  ", result["answer"])
    print("Source:  ", result["source"])
    _, metrics = train(data, quick=True)
    print(f"Retrieval hit rate: {metrics['retrieval_hit_rate']:.2f}")
