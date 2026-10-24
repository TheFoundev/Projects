"""A tiny SQL model runner with ref substitution.

The order of the models comes from the `{{ ref() }}` calls in the SQL files,
not from a list that is written by hand, and the manifest says which model
depends on which.
"""
import json
import re
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

REF = re.compile(r"\{\{\s*ref\('([^']+)'\)\s*\}\}")
MODEL_DIR = Path(__file__).resolve().parent.parent / "models"


def model_names():
    """The models of the project, from the files in the models directory."""
    return sorted(path.stem for path in MODEL_DIR.glob("*.sql"))


def dependencies(sql):
    """The models a model needs, from the refs in its SQL."""
    return sorted(set(REF.findall(sql)))


def order_models(models=None, sql_dir=None):
    """The models in the order they have to run.

    The order comes from the ref graph, so a model only runs after the models
    it needs. A model that needs a model that is not there, and a cycle, are
    errors.
    """
    models = list(models or model_names())
    sql_dir = Path(sql_dir or MODEL_DIR)

    sql_of = {}
    for name in models:
        path = sql_dir / f"{name}.sql"
        if not path.exists():
            raise ValueError(f"the model {name} has no file")
        sql_of[name] = path.read_text(encoding="utf-8")

    needs = {name: dependencies(sql) for name, sql in sql_of.items()}
    for name, wanted in needs.items():
        for need in wanted:
            if need not in sql_of:
                raise ValueError(f"the model {name} needs {need}, which does not exist")

    ordered = []
    done = set()
    while len(ordered) < len(models):
        progress = False
        for name in models:
            if name in done:
                continue
            if all(need in done for need in needs[name]):
                ordered.append(name)
                done.add(name)
                progress = True
        if not progress:
            raise ValueError("the models have a cycle")
    return ordered


def render(sql, available):
    """The SQL of a model, with the refs replaced by the tables.

    A ref that names a model that is not there is an error, and not a table
    that does not exist.
    """
    def replace(match):
        name = match.group(1)
        if name not in available:
            raise ValueError(f"the model needs {name}, which is not there")
        return name

    return REF.sub(replace, sql).strip().rstrip(";")


def make_raw():
    """The raw tables the models are built from."""
    rng = np.random.default_rng(7)
    customers = pd.DataFrame({
        "customer_id": np.arange(1, 41),
        "country": rng.choice(["CA", "US", "UK", "DE"], 40),
        "signup_date": pd.Timestamp("2025-06-01") + pd.to_timedelta(rng.integers(0, 180, 40), unit="D"),
    })
    orders = pd.DataFrame({
        "order_id": np.arange(1000, 1320),
        "customer_id": rng.integers(1, 41, 320),
        "order_ts": pd.Timestamp("2026-01-01") + pd.to_timedelta(rng.integers(0, 20 * 24 * 60, 320), unit="m"),
        "status": rng.choice(["paid", "paid", "paid", "pending", "refunded"], 320),
        "quantity": rng.integers(1, 4, 320),
        "unit_price": np.round(rng.uniform(6, 70, 320), 2),
    })
    return customers, orders


def run(quick=False, base_dir="artifacts"):
    """Materialise every model and write the manifest."""
    base = Path(base_dir)
    base.mkdir(parents=True, exist_ok=True)
    db_path = base / "warehouse.db"
    customers, orders = make_raw()
    if quick:
        customers = customers.head(20)
        orders = orders.head(120)

    connection = sqlite3.connect(db_path)
    customers.to_sql("raw_customers", connection, if_exists="replace", index=False)
    orders.to_sql("raw_orders", connection, if_exists="replace", index=False)
    connection.commit()

    order = order_models()
    manifest = {"raw_tables": ["raw_customers", "raw_orders"], "models": []}
    built = {"raw_customers", "raw_orders"}

    for model in order:
        sql_path = MODEL_DIR / f"{model}.sql"
        sql = render(sql_path.read_text(encoding="utf-8"), built)
        frame = pd.read_sql_query(sql, connection)
        frame.to_sql(model, connection, if_exists="replace", index=False)
        built.add(model)
        manifest["models"].append({
            "name": model,
            "rows": int(len(frame)),
            "sql_file": f"models/{model}.sql",
            "depends_on": dependencies(sql_path.read_text(encoding="utf-8")),
        })
    connection.commit()
    connection.close()

    (base / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    daily = pd.read_sql_query(
        "SELECT COUNT(*) AS rows, ROUND(SUM(revenue), 2) AS revenue FROM daily_revenue",
        sqlite3.connect(db_path),
    )
    return {
        "models": len(order),
        "raw_orders": int(len(orders)),
        "staging_rows": next(item["rows"] for item in manifest["models"] if item["name"] == "staging_orders"),
        "revenue": float(daily.loc[0, "revenue"] or 0),
        "manifest": str(base / "manifest.json"),
    }


def demo(base_dir="artifacts"):
    summary = run(quick=True, base_dir=base_dir)
    manifest = json.loads((Path(base_dir) / "manifest.json").read_text())
    for item in manifest["models"]:
        needs = ", ".join(item["depends_on"]) or "-"
        print(f"  {item['name']:24s} rows={item['rows']:4d}  needs={needs}")
    print(f"Raw orders: {summary['raw_orders']}, revenue: {summary['revenue']:.2f}")
