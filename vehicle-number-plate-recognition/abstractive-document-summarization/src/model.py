"""Extractive summarizer: score sentences with TF-IDF and keep the best ones.

The summary is extractive: the sentences of the document are scored against
the centre of the document and the best ones are kept. The length of the
summary is not written down somewhere: `train` searches over the lengths and
keeps the one that scores best on the corpus.
"""
import re

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.data import split_sentences

#: The lengths the training searches over.
LENGTHS = (1, 2, 3, 4)


def summarize(text, max_sentences=2):
    """The summary of a document: the sentences that say the most about it."""
    sentences = split_sentences(text)
    if len(sentences) <= max_sentences:
        return text

    vectorizer = TfidfVectorizer(stop_words="english")
    try:
        matrix = vectorizer.fit_transform(sentences)
    except ValueError:
        # Every word of the document is a stop word, so there is nothing to
        # rank. The first sentences are kept instead.
        return " ".join(sentences[:max_sentences])
    centroid = np.asarray(matrix.mean(axis=0))
    scores = cosine_similarity(matrix, centroid).ravel()

    # Prefer early sentences slightly, which is a cheap proxy for a lead paragraph.
    position_bonus = 0.06 / (np.arange(len(sentences)) + 1)
    scores = scores + position_bonus

    chosen = sorted(np.argsort(scores)[::-1][:max_sentences])
    return " ".join(sentences[index] for index in chosen)


def rouge_l(reference, candidate):
    """The longest common subsequence of the two texts, as a F1 score."""
    ref_tokens = re.findall(r"[a-z0-9']+", reference.lower())
    cand_tokens = re.findall(r"[a-z0-9']+", candidate.lower())
    if not ref_tokens or not cand_tokens:
        return 0.0

    table = [[0] * (len(cand_tokens) + 1) for _ in range(len(ref_tokens) + 1)]
    for i, ref_word in enumerate(ref_tokens, start=1):
        for j, cand_word in enumerate(cand_tokens, start=1):
            if ref_word == cand_word:
                table[i][j] = table[i - 1][j - 1] + 1
            else:
                table[i][j] = max(table[i - 1][j], table[i][j - 1])

    common = table[-1][-1]
    precision = common / len(cand_tokens)
    recall = common / len(ref_tokens)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def score_length(data, length, documents=None, references=None):
    """The ROUGE-L of a length over the corpus."""
    documents = documents if documents is not None else data["documents"]
    references = references if references is not None else data["references"]
    scores = [
        rouge_l(reference, summarize(document, max_sentences=length))
        for document, reference in zip(documents, references)
    ]
    return float(np.mean(scores)) if scores else 0.0


def search_length(data, lengths=LENGTHS):
    """Search the length of the summary over the corpus.

    The length that scores best is the one that is kept, and the scores of
    every length are returned so the search can be looked at.
    """
    results = {}
    best_length = None
    best_score = -1.0

    for length in lengths:
        score = score_length(data, length)
        results[length] = round(score, 4)
        if score > best_score:
            best_score = score
            best_length = length

    return best_length, round(best_score, 4), results


def train(data, quick=False):
    """Fit the summarizer: search the length that scores best."""
    lengths = LENGTHS if not quick else LENGTHS[:2]
    best_length, best_score, results = search_length(data, lengths)

    model = {
        "max_sentences": best_length,
        "lengths_searched": list(lengths),
        "scores_by_length": results,
    }
    return model, {
        "rouge_l": round(best_score, 4),
        "documents": len(data["documents"]),
        "max_sentences": best_length,
        "scores_by_length": results,
    }


def demo(data):
    model, metrics = train(data, quick=True)
    document = data["documents"][0]
    print("Original document:\n")
    print(document)
    print(f"\nSummary (the best length is {model['max_sentences']} sentences, ROUGE-L {metrics['rouge_l']}):\n")
    print(summarize(document, max_sentences=model["max_sentences"]))
    print("\nThe scores of every length:")
    for length, score in sorted(model["scores_by_length"].items()):
        print(f"  {length} sentences: {score:.4f}")
