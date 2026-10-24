"""Synthetic ratings with a few popular items."""
import numpy as np
import pandas as pd

GENRES = ["action", "comedy", "drama", "scifi", "documentary"]


def load_data(seed=42, quick=False):
    rng = np.random.default_rng(seed)
    n_users = 30 if quick else 55
    n_items = 24
    item_genre = rng.integers(0, len(GENRES), n_items)
    popularity = rng.normal(0, 0.8, n_items)
    user_taste = rng.normal(0, 0.7, (n_users, len(GENRES)))

    rows = []
    for user in range(n_users):
        for item in range(n_items):
            if rng.random() < 0.4:
                rating = 3.2 + user_taste[user, item_genre[item]] + popularity[item] + rng.normal(0, 0.6)
                rows.append((user, item, float(np.clip(rating, 1, 5))))

    ratings = pd.DataFrame(rows, columns=["user_id", "item_id", "rating"])
    ratings = ratings.sample(frac=1, random_state=seed).reset_index(drop=True)
    split = int(len(ratings) * 0.8)
    return {
        "train": ratings.iloc[:split].reset_index(drop=True),
        "test": ratings.iloc[split:].reset_index(drop=True),
        "n_users": n_users,
        "n_items": n_items,
        "titles": [f"Title {index:02d}" for index in range(n_items)],
    }
