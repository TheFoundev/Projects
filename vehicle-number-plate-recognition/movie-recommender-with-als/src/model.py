"""Biased matrix factorisation with SGD updates."""
import numpy as np


def fit(data, factors=8, epochs=16, learning_rate=0.015, regularization=0.04, seed=4):
    rng = np.random.default_rng(seed)
    n_users, n_items = data["n_users"], data["n_items"]
    global_mean = float(data["train"]["rating"].mean())
    user_bias = np.zeros(n_users)
    item_bias = np.zeros(n_items)
    user_factors = rng.normal(0, 0.1, (n_users, factors))
    item_factors = rng.normal(0, 0.1, (n_items, factors))

    rows = data["train"][["user_id", "item_id", "rating"]].to_numpy()
    for _ in range(epochs):
        rng.shuffle(rows)
        for user, item, rating in rows:
            user = int(user)
            item = int(item)
            prediction = (
                global_mean + user_bias[user] + item_bias[item]
                + float(user_factors[user] @ item_factors[item])
            )
            error = rating - prediction
            user_bias[user] += learning_rate * (error - regularization * user_bias[user])
            item_bias[item] += learning_rate * (error - regularization * item_bias[item])
            old_user = user_factors[user].copy()
            user_factors[user] += learning_rate * (error * item_factors[item] - regularization * user_factors[user])
            item_factors[item] += learning_rate * (error * old_user - regularization * item_factors[item])

    return {
        "global_mean": global_mean,
        "rating_range": (float(data["train"]["rating"].min()), float(data["train"]["rating"].max())),
        "user_bias": user_bias,
        "item_bias": item_bias,
        "user_factors": user_factors,
        "item_factors": item_factors,
        "seen": {
            int(user): set(group["item_id"].astype(int))
            for user, group in data["train"].groupby("user_id")
        },
    }


def predict(model, user, item):
    """The rating the model gives to an item, inside the range of the ratings."""
    value = (
        model["global_mean"] + model["user_bias"][user] + model["item_bias"][item]
        + float(model["user_factors"][user] @ model["item_factors"][item])
    )
    low, high = model.get("rating_range", (0.0, 5.0))
    return float(min(high, max(low, value)))


def rmse(model, data):
    errors = [
        (row.rating - predict(model, int(row.user_id), int(row.item_id))) ** 2
        for row in data["test"].itertuples()
    ]
    return float(np.sqrt(np.mean(errors)))


def recommend(model, data, user, count=5):
    seen = model["seen"].get(user, set())
    scores = [(item, predict(model, user, item)) for item in range(data["n_items"]) if item not in seen]
    return sorted(scores, key=lambda pair: pair[1], reverse=True)[:count]


def precision_at_5(model, data):
    """The share of the recommended items that are relevant.

    A recommendation is relevant when the test set says the user liked it.
    The denominator is the number of recommendations that were made, so the
    score is a share between zero and one.
    """
    relevant = data["test"][data["test"]["rating"] >= 4]
    hits = 0
    total = 0
    for user, group in relevant.groupby("user_id"):
        if int(user) >= data["n_users"]:
            continue
        recommended = {item for item, _ in recommend(model, data, int(user), 5)}
        truth = set(group["item_id"].astype(int))
        hits += len(recommended & truth)
        total += len(recommended)
    return hits / max(1, total)


def train(data, quick=False):
    model = fit(data, epochs=8 if quick else 16)
    return model, {
        "rmse": round(rmse(model, data), 4),
        "precision_at_5": round(float(precision_at_5(model, data)), 4),
        "users": int(data["n_users"]),
        "movies": int(data["n_items"]),
    }


def demo(data):
    model = fit(data, epochs=8)
    movies = data["movies"].set_index("item_id")
    print("Recommendations for user 0:")
    for item, score in recommend(model, data, 0):
        print(f"  {movies.loc[item, 'title']:18s} ({movies.loc[item, 'genre']})  predicted={score:.2f}")
