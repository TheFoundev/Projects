"""Hybrid recommender: SVD collaborative scores plus a tag profile."""
import numpy as np
from sklearn.decomposition import TruncatedSVD


def build_matrix(data):
    matrix = np.zeros((data["n_users"], data["n_items"]))
    for row in data["train"].itertuples():
        matrix[int(row.user_id), int(row.item_id)] = row.rating
    return matrix


def normalized(matrix):
    norms = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-9
    return matrix / norms


def fit(data):
    matrix = build_matrix(data)
    svd = TruncatedSVD(n_components=8, random_state=2)
    user_factors = svd.fit_transform(matrix)
    item_factors = svd.components_
    collaborative = user_factors @ item_factors
    collaborative = normalized(collaborative)

    tags = data["tags"]
    profiles = np.zeros((data["n_users"], tags.shape[1]))
    for row in data["train"].itertuples():
        if row.rating >= 4:
            profiles[int(row.user_id)] += tags[int(row.item_id)]
    profiles = normalized(profiles)
    content = normalized(profiles @ tags.T)

    hybrid = 0.7 * collaborative + 0.3 * content
    return {"hybrid": hybrid, "seen": matrix > 0}


def recommend(model, data, user, count=5):
    scores = model["hybrid"][user].copy()
    scores[model["seen"][user]] = -np.inf
    order = np.argsort(scores)[::-1][:count]
    return [(int(index), float(scores[index])) for index in order]


def precision_at_k(model, data, k=5):
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
        recommended = {item for item, _ in recommend(model, data, int(user), k)}
        truth = set(group["item_id"].astype(int))
        hits += len(recommended & truth)
        total += len(recommended)
    return hits / max(1, total)


def train(data, quick=False):
    model = fit(data)
    return model, {
        "precision_at_5": round(float(precision_at_k(model, data, 5)), 4),
        "users": int(data["n_users"]),
        "train_ratings": int(len(data["train"])),
        "test_ratings": int(len(data["test"])),
    }


def demo(data):
    model = fit(data)
    titles = data["items"]["title"].tolist()
    print("Recommendations for user 0:")
    for item, score in recommend(model, data, 0):
        print(f"  {titles[item]:24s} score={score:.3f}")
