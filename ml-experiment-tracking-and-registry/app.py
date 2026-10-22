"""Read the local run registry over HTTP."""
import json

from fastapi import FastAPI

from src.data import load_data
from src.model import best_run, ensure_db, train

app = FastAPI(title="Experiment registry")
DATA = load_data(seed=2, quick=True)


@app.get("/")
def root():
    return {"service": "experiment-registry", "storage": "artifacts/registry.db"}


@app.post("/train")
def run_training():
    _, metrics = train(DATA, quick=True)
    return metrics


@app.get("/runs")
def runs():
    connection = ensure_db()
    rows = connection.execute(
        "SELECT id, name, params, accuracy, f1, artefact FROM runs ORDER BY id"
    ).fetchall()
    connection.close()
    return [
        {"id": row[0], "name": row[1], "params": json.loads(row[2]),
         "accuracy": row[3], "f1": row[4], "artefact": row[5]}
        for row in rows
    ]


@app.get("/best")
def best():
    return best_run() or {"message": "no runs yet"}
