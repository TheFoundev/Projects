"""Minimal FastAPI wrapper around the random search."""
import json

from fastapi import FastAPI
from pydantic import BaseModel

from src.data import load_data
from src.model import ensure_db, run_search

app = FastAPI(title="Hyperparameter search service")
DATA = load_data(seed=1, quick=True)


class SearchRequest(BaseModel):
    trials: int = 4
    seed: int = 7


@app.get("/")
def root():
    return {"service": "hyperparameter-search", "space": "random forest", "trials": 4}


@app.post("/search")
def search(request: SearchRequest):
    _, metrics = run_search(DATA, trials=max(1, min(20, request.trials)), seed=request.seed)
    return metrics


@app.get("/trials")
def trials():
    connection = ensure_db("artifacts/trials.db")
    rows = connection.execute("SELECT id, params, accuracy, f1 FROM trials ORDER BY id").fetchall()
    connection.close()
    return [
        {"id": row[0], "params": json.loads(row[1]), "accuracy": row[2], "f1": row[3]}
        for row in rows
    ]
