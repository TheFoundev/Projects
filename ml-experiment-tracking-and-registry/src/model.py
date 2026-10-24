"""Run three models and store their results in a SQLite registry."""
import json
import pickle
import sqlite3
from pathlib import Path

from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def ensure_db(path="artifacts/registry.db"):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute(
        "CREATE TABLE IF NOT EXISTS runs ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, params TEXT, "
        "accuracy REAL, f1 REAL, artefact TEXT)"
    )
    connection.commit()
    return connection


def candidates(quick=False):
    return {
        "logistic": make_pipeline(StandardScaler(), LogisticRegression(max_iter=400)),
        "forest": RandomForestClassifier(n_estimators=30 if quick else 100, max_depth=6, random_state=4),
        "boosting": GradientBoostingClassifier(n_estimators=30 if quick else 90, max_depth=3, random_state=4),
    }


def train(data, quick=False):
    connection = ensure_db()
    best = None
    for name, model in candidates(quick).items():
        model.fit(data["X_train"], data["y_train"])
        prediction = model.predict(data["X_test"])
        accuracy = float(accuracy_score(data["y_test"], prediction))
        f1 = float(f1_score(data["y_test"], prediction))
        params = model.get_params() if hasattr(model, "get_params") else {}

        Path("artifacts/models").mkdir(parents=True, exist_ok=True)
        artefact = f"artifacts/models/{name}.pkl"
        with open(artefact, "wb") as handle:
            pickle.dump(model, handle)

        connection.execute(
            "INSERT INTO runs (name, params, accuracy, f1, artefact) VALUES (?, ?, ?, ?, ?)",
            (name, json.dumps({"model": name}), accuracy, f1, artefact),
        )
        if best is None or accuracy > best[0]:
            best = (accuracy, name, model, f1)

    connection.commit()
    count = connection.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    connection.close()
    return best[2], {
        "best_model": best[1],
        "best_accuracy": round(best[0], 4),
        "best_f1": round(best[3], 4),
        "runs_logged": int(count),
    }


def best_run(path="artifacts/registry.db"):
    connection = ensure_db(path)
    row = connection.execute(
        "SELECT name, accuracy, f1, artefact FROM runs ORDER BY accuracy DESC LIMIT 1"
    ).fetchone()
    connection.close()
    if row is None:
        return None
    return {"name": row[0], "accuracy": row[1], "f1": row[2], "artefact": row[3]}


def demo(data):
    model, metrics = train(data, quick=True)
    print("Best run in this demo:", metrics["best_model"])
    print(f"Accuracy: {metrics['best_accuracy']:.3f}, F1: {metrics['best_f1']:.3f}")
    print("Registry row:", best_run())
