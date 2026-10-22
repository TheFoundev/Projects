"""Synthetic movie ratings with genre preferences."""
import numpy as np
import pandas as pd

MOVIES = [
    ("Signal Drift", "sci-fi"), ("The Long Weekend", "comedy"), ("Quiet Harbour", "drama"),
    ("Last Train North", "thriller"), ("Paper Planets", "sci-fi"), ("Kitchen Table", "drama"),
    ("Deep Field", "documentary"), ("Summer Repair", "comedy"), ("The Cartographer", "adventure"),
    ("Night Bus", "thriller"), ("Small Machines", "sci-fi"), ("Field Notes", "documentary"),
    ("Atlas of Rain", "drama"), ("The Understudy", "comedy"), ("Orbit Cafe", "sci-fi"),
    ("Second Draft", "drama"), ("Blue Hour", "thriller"), ("The Archive", "documentary"),
    ("Roadside Stand", "comedy"), ("Winter Circuit", "adventure"), ("Half Light", "drama"),
    ("Local Maximum", "sci-fi"), ("The Return Trip", "adventure"), ("Open Studio", "documentary"),
    ("Static Garden", "sci-fi"), ("Borrowed Time", "thriller"), ("Mountain Post", "adventure"),
    ("The Listening Room", "drama"), ("Parallel Lines", "sci-fi"), ("Good Company", "comedy"),
]


def load_data(seed=42, quick=False):
    rng = np.random.default_rng(seed)
    n_users = 35 if quick else 70
    n_items = 30
    genres = sorted({genre for _, genre in MOVIES})
    genre_index = {genre: index for index, genre in enumerate(genres)}
    item_genre = np.array([genre_index[genre] for _, genre in MOVIES])
    user_pref = rng.normal(0, 0.7, (n_users, len(genres)))

    rows = []
    for user in range(n_users):
        for item in range(n_items):
            if rng.random() < 0.35:
                score = 3.3 + user_pref[user, item_genre[item]] + rng.normal(0, 0.7)
                rows.append((user, item, float(np.clip(score, 1, 5))))

    ratings = pd.DataFrame(rows, columns=["user_id", "item_id", "rating"])
    ratings = ratings.sample(frac=1, random_state=seed).reset_index(drop=True)
    split = int(len(ratings) * 0.8)
    movies = pd.DataFrame({
        "item_id": np.arange(n_items),
        "title": [title for title, _ in MOVIES],
        "genre": [genre for _, genre in MOVIES],
    })
    return {
        "train": ratings.iloc[:split].reset_index(drop=True),
        "test": ratings.iloc[split:].reset_index(drop=True),
        "movies": movies,
        "n_users": n_users,
        "n_items": n_items,
    }
