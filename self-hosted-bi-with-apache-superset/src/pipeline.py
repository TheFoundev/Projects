"""Build a SQLite warehouse and execute saved BI queries."""
import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

QUERIES = ["monthly_revenue", "top_products", "region_share", "repeat_rate"]
SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def make_orders(count=500, seed=12):
    rng = np.random.default_rng(seed)
    start = pd.Timestamp("2026-01-01")
    dates = start + pd.to_timedelta(rng.integers(0, 150, count), unit="D")
    frame = pd.DataFrame({
        "order_id": np.arange(1, count + 1),
        "customer_id": rng.integers(1, 80, count),
        "order_date": dates.strftime("%Y-%m-%d"),
        "region": rng.choice(["north", "south", "east", "west"], count),
        "product": rng.choice(["widget", "gadget", "cable", "stand", "sensor"], count),
        "quantity": rng.integers(1, 5, count),
        "unit_price": np.round(rng.uniform(5, 95, count), 2),
        "status": rng.choice(["paid", "paid", "paid", "pending", "refunded"], count),
    })
    return frame


def run(quick=False, base_dir="artifacts"):
    base = Path(base_dir)
    base.mkdir(parents=True, exist_ok=True)
    orders = make_orders(180 if quick else 700)
    db_path = base / "bi_warehouse.db"
    connection = sqlite3.connect(db_path)
    orders.to_sql("orders", connection, if_exists="replace", index=False)
    connection.commit()

    dashboard = {}
    for name in QUERIES:
        sql = (SQL_DIR / f"{name}.sql").read_text(encoding="utf-8").strip().rstrip(";")
        frame = pd.read_sql_query(sql, connection)
        dashboard[name] = frame.to_dict(orient="records")

    monthly = pd.DataFrame(dashboard["monthly_revenue"])
    if not monthly.empty:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axis = plt.subplots(figsize=(7, 3.2))
        axis.bar(monthly["month"], monthly["revenue"], color="#7c3aed")
        axis.set_title("Monthly revenue")
        axis.set_ylabel("revenue")
        axis.tick_params(axis="x", rotation=30)
        fig.tight_layout()
        fig.savefig(base / "monthly_revenue.png", dpi=120)
        plt.close(fig)

    repeat = dashboard["repeat_rate"][0]["repeat_rate"] if dashboard["repeat_rate"] else 0
    total = float(orders.loc[orders["status"] == "paid", "quantity"].mul(
        orders.loc[orders["status"] == "paid", "unit_price"]).sum())
    (base / "dashboard.json").write_text(json.dumps(dashboard, indent=2), encoding="utf-8")
    return {
        "queries": len(QUERIES),
        "orders": int(len(orders)),
        "revenue": round(total, 2),
        "repeat_rate": float(repeat or 0),
        "dashboard": str(base / "dashboard.json"),
        "chart": str(base / "monthly_revenue.png"),
    }


def demo(base_dir="artifacts"):
    summary = run(quick=True, base_dir=base_dir)
    dashboard = json.loads((Path(base_dir) / "dashboard.json").read_text())
    for name in QUERIES:
        print(f"\n{name}:")
        print(pd.DataFrame(dashboard[name]).to_string(index=False))
    print(f"\nRevenue: {summary['revenue']:.2f}, repeat rate: {summary['repeat_rate']:.1f}%")
