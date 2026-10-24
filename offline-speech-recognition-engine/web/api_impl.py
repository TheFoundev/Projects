"""The API of the offline recogniser.

The recogniser of the project is used as it is: a word is synthesised as a
pair of tones, the sound is cut into frames of log-band features and the
nearest template is found with a dynamic time warping distance. The accuracy
on the held-out samples is the share of the words the matcher names right.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.data import frame_features, load_data, synthesize  # noqa: E402
from src.model import dtw_distance, train  # noqa: E402

#: The fitted templates, kept between the calls.
_CACHE: dict[int, tuple] = {}


def _state(seed: int = 42):
    """The data, the templates and the metrics of the run."""
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


def _per_word(data, model) -> list[dict]:
    """The accuracy of the matcher on every word of the vocabulary."""
    hits = {word: 0 for word in data["words"]}
    totals = {word: 0 for word in data["words"]}
    for word, features in data["test"]:
        distances = {candidate: dtw_distance(features, template)
                     for candidate, template in model["templates"].items()}
        prediction = min(distances, key=distances.get)
        totals[word] += 1
        hits[word] += int(prediction == word)
    return [
        {"word": word, "samples": totals[word], "hits": hits[word],
         "accuracy": round(hits[word] / max(1, totals[word]), 4)}
        for word in data["words"]
    ]


def summary():
    data, model, metrics = _state()
    rows = _per_word(data, model)
    return {
        "stats": {
            "accuracy": metrics["accuracy"],
            "vocabulary": metrics["vocabulary_size"],
            "test_samples": metrics["test_samples"],
            "frames": int(model["templates"][data["words"][0]].shape[0]),
        },
        "series": [{"label": row["word"], "value": row["accuracy"]} for row in rows],
        "lists": {"vocabulary": rows},
    }


def handle(method, path, payload, user):
    if method == "POST" and path == "/api/recognize":
        word = str((payload or {}).get("word", "")).strip().lower()
        if not word:
            return 400, {"error": "no word was sent"}
        seed = _number(payload, "seed", 42)
        data, model, _ = _state(seed)
        if word not in data["words"]:
            return 400, {"error": f"the vocabulary is: {', '.join(data['words'])}"}
        # A fresh sample of the word, so the matcher has to hear it.
        sample = frame_features(synthesize(word, seed=9999))
        distances = {candidate: round(float(dtw_distance(sample, template)), 4)
                     for candidate, template in model["templates"].items()}
        ranked = sorted(distances.items(), key=lambda pair: pair[1])
        return 200, {
            "spoken": word,
            "heard": ranked[0][0],
            "correct": ranked[0][0] == word,
            "distances": ranked,
        }

    if method == "POST" and path == "/api/train":
        seed = _number(payload, "seed", 42)
        _CACHE.pop(seed, None)
        state = summary()
        return 200, {"retrained": True, "summary": state}

    return 404, {"error": "not found"}
