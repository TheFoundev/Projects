"""The API of the project: the precision of the hybrid scorer and the lists.

The numbers come from the real core of the project: `src.model.fit` builds
the collaborative scores of the truncated SVD and the content scores of the
tag profiles, and `src.model.precision_at_k` measures the mix on the
held-out ratings.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data import GENRES, load_data  # noqa: E402
from src.model import fit, precision_at_k, recommend, train  # noqa: E402

#: The model, the data and the metrics of the last run.
_STATE: dict = {}


def state() -> dict:
    """Fit the hybrid scorer once for the process."""
    if "model" not in _STATE:
        data = load_data(seed=42, quick=False)
        model, metrics = train(data, quick=False)
        _STATE["data"] = data
        _STATE["model"] = model
        _STATE["metrics"] = metrics
    return _STATE


def recommendation_rows(user: int, count: int = 5) -> list:
    """The recommended items of a user, with the score and the genres."""
    current = state()
    data = current["data"]
    titles = data["items"]["title"].tolist()
    rows = []
    for item, score in recommend(current["model"], data, user, count):
        genres = [
            genre for genre in GENRES if int(data["items"].iloc[item][genre]) == 1
        ]
        rows.append({
            "item": titles[item],
            "score": round(float(score), 4),
            "genres": ", ".join(genres) or "-",
        })
    return rows


def summary() -> dict:
    """The state of the recommender: the precision, the catalogue and the list."""
    current = state()
    metrics = current["metrics"]
    rows = recommendation_rows(0)
    return {
        "stats": {
            "precision_at_5": metrics["precision_at_5"],
            "users": metrics["users"],
            "items": int(current["data"]["n_items"]),
            "train_ratings": metrics["train_ratings"],
        },
        "series": [
            {"label": row["item"], "value": row["score"]} for row in rows
        ],
        "lists": {
            "recommendations": rows,
        },
    }


def handle(method, path, payload, user):
    """The read and the write endpoints of the project."""
    if method == "GET" and path == "/api/recommendations":
        try:
            user_id = int(payload.get("user", 0)) if payload else 0
        except (TypeError, ValueError):
            user_id = 0
        return 200, {"user": user_id, "recommendations": recommendation_rows(user_id)}
    if method == "POST" and path == "/api/recommend":
        try:
            user_id = int(payload.get("user", 0))
        except (TypeError, ValueError):
            return 400, {"error": "the user must be a number"}
        data = state()["data"]
        if user_id < 0 or user_id >= int(data["n_users"]):
            return 400, {"error": f"unknown user {user_id} (0..{int(data['n_users']) - 1})"}
        rows = recommendation_rows(user_id)
        return 200, {
            "user": user_id,
            "recommendations": rows,
            "precision_at_5": round(float(precision_at_k(state()["model"], data, 5)), 4),
        }
    if method == "POST" and path == "/api/train":
        data = load_data(seed=42, quick=False)
        model, metrics = train(data, quick=False)
        _STATE["data"], _STATE["model"], _STATE["metrics"] = data, model, metrics
        return 200, metrics
    return 404, {"error": "not found"}
