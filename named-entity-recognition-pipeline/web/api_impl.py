"""The API of the entity recognizer.

The classifier of the project does the work: a sentence is turned into
per-token features, the logistic regression of the project labels every
token, and the spans of the project turn the labels into entities. The
metrics come from the same evaluation the project uses.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.data import load_data  # noqa: E402
from src.model import spans, token_features, train  # noqa: E402

#: The fitted classifier, kept between the calls.
_CACHE: dict[int, tuple] = {}


def _state(seed: int = 42):
    """The data, the fitted model and the metrics of the run."""
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


def _tokens(text: str) -> list[str]:
    """The tokens of a sentence, the way the project splits them."""
    return text.replace(".", " .").split()


def _predict(model, tokens: list[str]) -> list[str]:
    """The label the classifier gives to every token of a sentence."""
    rows = [token_features(tokens, index) for index in range(len(tokens))]
    return list(model["classifier"].predict(model["vectorizer"].transform(rows)))


def _per_label_scores(data, model) -> list[dict]:
    """The precision, the recall and the F1 of every entity type."""
    found = {}
    for example in data["test"]:
        tokens = example["tokens"]
        truth = spans(tokens, example["labels"])
        predicted = spans(tokens, _predict(model, tokens))
        for kind in data["labels"]:
            true_spans = {span for span in truth if span[0] == kind}
            pred_spans = {span for span in predicted if span[0] == kind}
            hits = len(true_spans & pred_spans)
            row = found.setdefault(kind, {"hits": 0, "true": 0, "predicted": 0})
            row["hits"] += hits
            row["true"] += len(true_spans)
            row["predicted"] += len(pred_spans)

    rows = []
    for kind, row in found.items():
        precision = row["hits"] / max(1, row["predicted"])
        recall = row["hits"] / max(1, row["true"])
        f1 = 2 * precision * recall / max(1e-9, precision + recall)
        rows.append({"type": kind, "precision": round(precision, 4),
                     "recall": round(recall, 4), "f1": round(f1, 4)})
    rows.sort(key=lambda row: row["type"])
    return rows


def summary():
    data, model, metrics = _state()
    example = data["test"][0]
    tokens = example["tokens"]
    predicted = _predict(model, tokens)
    entities = sorted(spans(tokens, predicted))

    return {
        "stats": {
            "entity_f1": metrics["entity_f1"],
            "entity_precision": metrics["entity_precision"],
            "entity_recall": metrics["entity_recall"],
            "tokens": metrics["tokens"],
        },
        "series": [{"label": row["type"], "value": row["f1"]} for row in _per_label_scores(data, model)],
        "lists": {
            "entities": [{"type": kind, "text": text} for kind, text in entities],
            "types": _per_label_scores(data, model),
            "tokens": [
                {"token": token, "true": truth, "predicted": guess}
                for token, truth, guess in zip(tokens, example["labels"], predicted)
            ],
        },
    }


def handle(method, path, payload, user):
    if method == "POST" and path == "/api/tag":
        text = str((payload or {}).get("text", "")).strip()
        if not text:
            return 400, {"error": "no text was sent"}
        seed = _number(payload, "seed", 42)
        data, model, _ = _state(seed)
        tokens = _tokens(text)
        predicted = _predict(model, tokens)
        entities = sorted(spans(tokens, predicted))
        return 200, {
            "text": text,
            "tokens": [{"token": token, "label": label} for token, label in zip(tokens, predicted)],
            "entities": [{"type": kind, "text": value} for kind, value in entities],
        }

    if method == "POST" and path == "/api/train":
        seed = _number(payload, "seed", 42)
        _CACHE.pop(seed, None)
        state = summary()
        return 200, {"retrained": True, "summary": state}

    return 404, {"error": "not found"}
