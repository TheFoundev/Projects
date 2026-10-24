"""Synthetic ratings plus item tags for a hybrid recommender."""
import numpy as np
import pandas as pd

GENRES = ["sci-fi", "comedy", "drama", "action", "documentary", "family"]

TITLES = [
    "Signal Drift", "The Long Weekend", "Quiet Harbour", "Last Train North", "Paper Planets",
    "Kitchen Table", "Deep Field", "Summer Repair", "The Cartographer", "Night Bus",
    "Small Machines", "Field Notes", "Atlas of Rain", "The Understudy", "Orbit Cafe",
    "Second Draft", "Blue Hour", "The Archive", "Roadside Stand", "Winter Circuit",
    "Half Light", "Local Maximum", "The Return Trip", "Open Studio", "Static Garden",
    "Borrowed Time", "Mountain Post", "The Listening Room", "Parallel Lines", "Good Company",
]


def make_catalog(n_items=30, seed=42):
    rng = np.random.default_rng(seed)
    tags = (rng.random((n_items, len(GENRES))) < 0.32).astype(float)
    for row in tags:
        if row.sum() == 0:
            row[rng.integers(0, len(GENRES))] = 1
    items = pd.DataFrame({
        "item_id": np.arange(n_items),
        "title": TITLES[:n_items],
    })
    for index, genre in enumerate(GENRES):
        items[genre] = tags[:, index].astype(int)
    return items, tags


def load_data(seed=42, quick=False):
    rng = np.random.default_rng(seed)
    n_users = 30 if quick else 60
    n_items = 30
    items, tags = make_catalog(n_items, seed)
    user_preferences = rng.normal(0, 1, (n_users, len(GENRES)))

    rows = []
    for user in range(n_users):
        affinity = user_preferences[user] @ tags.T
        affinity = (affinity - affinity.mean()) / (affinity.std() + 1e-9)
        for item in range(n_items):
            if rng.random() < 0.32:
                rating = 3 + 1.15 * affinity[item] + rng.normal(0, 0.75)
                rows.append((user, item, float(np.clip(rating, 1, 5))))

    ratings = pd.DataFrame(rows, columns=["user_id", "item_id", "rating"])
    ratings = ratings.sample(frac=1, random_state=seed).reset_index(drop=True)
    split = int(len(ratings) * 0.8)
    return {
        "items": items,
        "tags": tags,
        "train": ratings.iloc[:split].reset_index(drop=True),
        "test": ratings.iloc[split:].reset_index(drop=True),
        "n_users": n_users,
        "n_items": n_items,
    }
