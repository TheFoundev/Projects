"""Four recommenders behind one evaluation loop."""
import numpy as np
from sklearn.decomposition import NMF, TruncatedSVD


def build_matrix(data):
    matrix = np.zeros((data["n_users"], data["n_items"]))
    for row in data["train"].itertuples():
        matrix[int(row.user_id), int(row.item_id)] = row.rating
    return matrix


def normalize(matrix):
    return matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-9)


def fit_all(data):
    matrix = build_matrix(data)
    seen = matrix > 0
    models = {}

    popularity = matrix.sum(axis=0)
    models["popularity"] = np.tile(popularity, (data["n_users"], 1))

    item_similarity = normalize(matrix.T) @ normalize(matrix.T).T
    models["item_item"] = matrix @ item_similarity

    for name, factory in [
        ("svd", lambda: TruncatedSVD(n_components=8, random_state=2)),
        ("nmf", lambda: NMF(n_components=8, random_state=2, init="nndsvda", max_iter=300)),
    ]:
        reducer = factory()
        user_factors = reducer.fit_transform(matrix)
        item_factors = reducer.components_
        models[name] = user_factors @ item_factors

    return {"scores": models, "seen": seen}


def recommend_matrix(scores, seen, user, k=5):
    values = scores[user].copy()
    values[seen[user]] = -np.inf
    return list(np.argsort(values)[::-1][:k])


def evaluate(model, data, k=5):
    """The metrics of every recommender.

    The precision is the share of the recommendations that were relevant, so
    the denominator is the number of recommendations that were made and not
    the number of users times k. The recall is the share of the relevant items
    that were found, and the coverage is the share of the catalogue that was
    recommended at all.
    """
    relevant = data["test"][data["test"]["rating"] >= 4]
    results = {}
    for name, scores in model["scores"].items():
        hits = 0
        total = 0
        found = 0
        covered = set()
        for user, group in relevant.groupby("user_id"):
            user = int(user)
            if user >= data["n_users"]:
                continue
            items = recommend_matrix(scores, model["seen"], user, k)
            covered.update(items)
            truth = set(group["item_id"].astype(int))
            hits += len(set(items) & truth)
            total += len(items)
            found += len(truth)
        results[name] = {
            "precision": hits / max(1, total),
            "recall": hits / max(1, found),
            "coverage": len(covered) / max(1, data["n_items"]),
        }
    return results


def train(data, quick=False):
    model = fit_all(data)
    results = evaluate(model, data)
    best = max(results, key=lambda name: results[name]["precision"])
    return model, {
        "best_method": best,
        "best_precision_at_5": round(float(results[best]["precision"]), 4),
        "best_recall_at_5": round(float(results[best]["recall"]), 4),
        "methods": len(results),
        "items": int(data["n_items"]),
    }


def demo(data):
    model, metrics = train(data, quick=True)
    results = evaluate(model, data)
    print(f"Best method: {metrics['best_method']}")
    for name, values in results.items():
        print(f"  {name:12s} P@5={values['precision']:.3f} R@5={values['recall']:.3f} coverage={values['coverage']:.2f}")
    best_scores = model["scores"][metrics["best_method"]]
    items = recommend_matrix(best_scores, model["seen"], 0)
    print("User 0 top 5:", [data["titles"][item] for item in items])
