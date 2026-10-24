"""Feature-based token classification with a logistic regression."""
import re

import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_recall_fscore_support


def token_features(tokens, index):
    token = tokens[index]
    lower = token.lower()
    features = {
        "bias": 1.0,
        "token": lower,
        "shape": re.sub(r"[a-z]", "x", re.sub(r"[A-Z]", "X", re.sub(r"[0-9]", "d", token))),
        "is_title": token[:1].isupper(),
        "is_digit": token.isdigit(),
        "prefix2": lower[:2],
        "suffix2": lower[-2:],
    }
    if index > 0:
        features["prev"] = tokens[index - 1].lower()
        features["prev_title"] = tokens[index - 1][:1].isupper()
    if index + 1 < len(tokens):
        features["next"] = tokens[index + 1].lower()
    return features


def featurize(examples):
    rows = []
    labels = []
    for example in examples:
        for index in range(len(example["tokens"])):
            rows.append(token_features(example["tokens"], index))
            labels.append(example["labels"][index])
    return rows, np.asarray(labels)


def spans(tokens, labels):
    """The entities of a labelled sentence.

    The labels may be plain ("PER") or in the BIO form ("B-PER", "I-PER"). A
    token that is marked as a continuation belongs to the entity before it,
    so "Ada Lovelace" is one entity and not two.
    """
    result = []
    current = None
    for token, label in zip(tokens, labels):
        if label == "O":
            if current:
                result.append(current)
                current = None
            continue

        # The BIO prefix says whether the entity starts or continues.
        prefix = ""
        kind = label
        if len(label) > 2 and label[1] == "-" and label[0] in ("B", "I", "S", "E"):
            prefix, kind = label[0], label[2:]

        starts_new = current is None
        if prefix == "I":
            starts_new = current is None or current[0] != kind
        elif prefix == "B":
            starts_new = True
        elif prefix == "S":
            starts_new = True
        elif prefix == "E":
            starts_new = current is None or current[0] != kind
        elif current is None or current[0] != kind:
            starts_new = True

        if starts_new:
            if current:
                result.append(current)
            current = [kind, len(result), token]
        else:
            current[2] += " " + token

        if prefix == "S" or prefix == "E":
            result.append(current)
            current = None

    if current:
        result.append(current)
    return {(label, text) for label, _, text in result}


def train(data, quick=False):
    train_rows, train_labels = featurize(data["train"])
    test_rows, test_labels = featurize(data["test"])
    vectorizer = DictVectorizer()
    X_train = vectorizer.fit_transform(train_rows)
    X_test = vectorizer.transform(test_rows)

    model = LogisticRegression(max_iter=500, C=2.0)
    model.fit(X_train, train_labels)
    predictions = model.predict(X_test)

    # Rebuild token-level examples for entity-level scoring.
    cursor = 0
    true_entities = set()
    predicted_entities = set()
    for example in data["test"]:
        length = len(example["tokens"])
        true_entities |= spans(example["tokens"], example["labels"])
        predicted_entities |= spans(example["tokens"], predictions[cursor:cursor + length])
        cursor += length

    correct = len(true_entities & predicted_entities)
    precision = correct / max(1, len(predicted_entities))
    recall = correct / max(1, len(true_entities))
    f1 = 2 * precision * recall / max(1e-9, precision + recall)
    return {"vectorizer": vectorizer, "classifier": model}, {
        "entity_precision": round(float(precision), 4),
        "entity_recall": round(float(recall), 4),
        "entity_f1": round(float(f1), 4),
        "tokens": int(len(test_labels)),
    }


def demo(data):
    model, metrics = train(data, quick=True)
    example = data["test"][0]
    rows = [token_features(example["tokens"], index) for index in range(len(example["tokens"]))]
    predictions = model["classifier"].predict(model["vectorizer"].transform(rows))
    print("Sentence:", " ".join(example["tokens"]))
    print("True:     ", list(zip(example["tokens"], example["labels"])))
    print("Predicted:", list(zip(example["tokens"], predictions)))
    print(f"Entity F1 on the test split: {metrics['entity_f1']:.3f}")
