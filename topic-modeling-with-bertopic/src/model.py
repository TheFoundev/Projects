"""TF-IDF plus NMF topic assignment."""
import numpy as np
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import TfidfVectorizer

def train(data, quick=False):
    vectorizer = TfidfVectorizer(stop_words="english", max_features=200)
    matrix = vectorizer.fit_transform(data["documents"])
    topics = 3 if quick else 4
    model = NMF(n_components=topics, random_state=5, init="nndsvda", max_iter=300)
    document_topics = model.fit_transform(matrix)
    terms = vectorizer.get_feature_names_out()

    topic_words = []
    for topic in model.components_:
        order = np.argsort(topic)[::-1][:4]
        topic_words.append([str(terms[index]) for index in order])

    assignments = document_topics.argmax(axis=1)
    confidence = float(np.mean(document_topics.max(axis=1) / (document_topics.sum(axis=1) + 1e-9)))
    return {
        "vectorizer": vectorizer,
        "nmf": model,
        "topics": topic_words,
        "assignments": assignments,
        "documents": data["documents"],
    }, {
        "topics": topics,
        "documents": len(data["documents"]),
        "mean_confidence": round(confidence, 4),
        "vocabulary": int(len(terms)),
    }

def demo(data):
    model, metrics = train(data, quick=True)
    print(f"Discovered {metrics['topics']} topics in {metrics['documents']} documents.")
    for index, words in enumerate(model["topics"]):
        examples = [doc for doc, topic in zip(model["documents"], model["assignments"]) if topic == index]
        print(f"Topic {index + 1}: {', '.join(words)}")
        if examples:
            print(f"  e.g. {examples[0]}")
    print(f"Mean assignment confidence: {metrics['mean_confidence']:.2f}")
