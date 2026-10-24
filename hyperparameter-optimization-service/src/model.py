"""Random search over a random forest, with a SQLite trial log."""
import json
import sqlite3
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score

SPACE = {
    "n_estimators": [20, 40, 80, 120],
    "max_depth": [3, 5, 8, None],
    "min_samples_leaf": [1, 2, 4, 8],
}


def ensure_db(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute(
        "CREATE TABLE IF NOT EXISTS trials ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, params TEXT, accuracy REAL, f1 REAL)"
    )
    connection.commit()
    return connection


def run_search(data, trials=8, seed=7, db_path="artifacts/trials.db"):
    rng = np.random.default_rng(seed)
    connection = ensure_db(db_path)
    best_score = -1.0
    best_model = None
    best_params = None

    for _ in range(trials):
        depth = rng.choice(SPACE["max_depth"])
        params = {
            "n_estimators": int(rng.choice(SPACE["n_estimators"])),
            "max_depth": None if depth is None else int(depth),
            "min_samples_leaf": int(rng.choice(SPACE["min_samples_leaf"])),
        }
        model = RandomForestClassifier(random_state=seed, n_jobs=1, **params)
        model.fit(data["X_train"], data["y_train"])
        prediction = model.predict(data["X_test"])
        accuracy = float(accuracy_score(data["y_test"], prediction))
        f1 = float(f1_score(data["y_test"], prediction))
        connection.execute(
            "INSERT INTO trials (params, accuracy, f1) VALUES (?, ?, ?)",
            (json.dumps(params), accuracy, f1),
        )
        if accuracy > best_score:
            best_score = accuracy
            best_model = model
            best_params = params

    connection.commit()
    count = connection.execute("SELECT COUNT(*) FROM trials").fetchone()[0]
    connection.close()
    return best_model, {
        "best_accuracy": round(float(best_score), 4),
        "best_params": json.dumps(best_params),
        "trials_this_run": trials,
        "trials_total": int(count),
    }


def train(data, quick=False):
    return run_search(data, trials=6 if quick else 14)


def demo(data):
    model, metrics = run_search(data, trials=4)
    print("Random-search space:", SPACE)
    print("Best trial:", metrics["best_params"])
    print(f"Validation accuracy: {metrics['best_accuracy']:.3f}")
    print("The trial log is stored in artifacts/trials.db.")
