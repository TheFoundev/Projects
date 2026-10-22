"""The API of the movie recommender.

The numbers are the real ones: the ratings are built, the biased matrix
factorisation is trained on them and the recommendations and the metrics come
out of the project's own code. Nothing is stored and nothing is faked; the
model is fitted in the process that answers the request.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.data import load_data  # noqa: E402
from src.model import recommend, train  # noqa: E402

#: The trained model, kept so a page does not train it again for every call.
_CACHE: dict[int, tuple] = {}


def _state(seed: int = 42):
    """The data, the trained model and the metrics of the run."""
    if seed not in _CACHE:
        data = load_data(seed=seed)
        model, metrics = train(data)
        _CACHE[seed] = (data, model, metrics)
    return _CACHE[seed]


def _number(payload, key: str, default: int) -> int:
    """One number of the request.

    The query string of a GET arrives as a dictionary of lists, so the first
    value of the list is taken.
    """
    value = (payload or {}).get(key, default)
    if isinstance(value, (list, tuple)):
        value = value[0] if value else default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _recommendations(data, model, user: int, count: int = 5) -> list[dict]:
    """The films the model proposes to one user."""
    movies = data["movies"].set_index("item_id")
    rows = []
    for item, score in recommend(model, data, user, count):
        rows.append({
            "title": str(movies.loc[item, "title"]),
            "genre": str(movies.loc[item, "genre"]),
            "predicted": round(float(score), 3),
        })
    return rows


def summary():
    data, model, metrics = _state()
    movies = data["movies"]
    recommendations = _recommendations(data, model, 0)

    # The mean of the training ratings per genre, straight from the data.
    merged = data["train"].merge(movies, left_on="item_id", right_on="item_id")
    per_genre = merged.groupby("genre")["rating"].agg(["count", "mean"]).reset_index()
    per_genre = per_genre.sort_values("count", ascending=False)

    return {
        "stats": {
            "movies": int(data["n_items"]),
            "users": int(data["n_users"]),
            "ratings": int(len(data["train"]) + len(data["test"])),
            "precision_at_5": metrics["precision_at_5"],
        },
        "series": [
            {"label": row["title"], "value": row["predicted"]}
            for row in recommendations
        ],
        "lists": {
            "recommendations": recommendations,
            "genres": [
                {"genre": str(row["genre"]), "ratings": int(row["count"]),
                 "mean_rating": round(float(row["mean"]), 3)}
                for _, row in per_genre.iterrows()
            ],
        },
    }


def handle(method, path, payload, user):
    if method == "GET" and path == "/api/recommendations":
        seed = _number(payload, "seed", 42)
        wanted = _number(payload, "user", 0)
        data, model, _ = _state(seed)
        return 200, {"user": wanted, "recommendations": _recommendations(data, model, wanted)}

    if method == "POST" and path == "/api/train":
        seed = _number(payload, "seed", 42)
        _CACHE.pop(seed, None)
        state = summary()
        return 200, {"retrained": True, "summary": state}

    return 404, {"error": "not found"}
