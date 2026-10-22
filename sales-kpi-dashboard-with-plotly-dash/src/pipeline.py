"""Sales KPI calculation and trend chart."""
import json
from pathlib import Path

import numpy as np
import pandas as pd


def make_sales(count=180, seed=42):
    rng = np.random.default_rng(seed)
    start = pd.Timestamp("2026-06-01")
    frame = pd.DataFrame({
        "order_id": np.arange(1, count + 1),
        "order_date": start + pd.to_timedelta(rng.integers(0, 90, count), unit="D"),
        "region": rng.choice(["north", "south", "east", "west"], count),
        "product": rng.choice(["widget", "gadget", "cable", "stand", "sensor"], count),
        "units": rng.integers(1, 6, count),
        "unit_price": np.round(rng.uniform(8, 120, count), 2),
    })
    frame["revenue"] = (frame["units"] * frame["unit_price"]).round(2)
    frame["order_date"] = frame["order_date"].dt.strftime("%Y-%m-%d")
    return frame


def run(quick=False, base_dir="artifacts"):
    base = Path(base_dir)
    base.mkdir(parents=True, exist_ok=True)
    sales = make_sales(70 if quick else 360)
    sales.to_csv(base / "sales.csv", index=False)
    sales["date"] = pd.to_datetime(sales["order_date"])

    revenue = float(sales["revenue"].sum())
    orders = int(len(sales))
    aov = round(revenue / max(1, orders), 2)
    latest = sales["date"].max()
    recent = sales[sales["date"] > latest - pd.Timedelta(days=30)]
    previous = sales[(sales["date"] <= latest - pd.Timedelta(days=30)) & (sales["date"] > latest - pd.Timedelta(days=60))]
    growth = round((recent["revenue"].sum() - previous["revenue"].sum()) / max(1.0, previous["revenue"].sum()) * 100, 2)

    daily = sales.groupby("date", as_index=False)["revenue"].sum().sort_values("date")
    by_product = sales.groupby("product", as_index=False)["revenue"].sum().sort_values("revenue", ascending=False)
    by_region = sales.groupby("region", as_index=False)["revenue"].sum().sort_values("revenue", ascending=False)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axis = plt.subplots(figsize=(8, 3.2))
    axis.plot(daily["date"], daily["revenue"], color="#0f766e", linewidth=1.8)
    axis.set_title("Daily revenue")
    axis.set_ylabel("revenue")
    axis.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(base / "revenue_trend.png", dpi=120)
    plt.close(fig)

    kpis = {
        "revenue": round(revenue, 2),
        "orders": orders,
        "aov": aov,
        "growth_pct": growth,
        "top_product": str(by_product.iloc[0]["product"]),
        "top_region": str(by_region.iloc[0]["region"]),
        "products": by_product.round(2).to_dict(orient="records"),
        "regions": by_region.round(2).to_dict(orient="records"),
    }
    (base / "kpis.json").write_text(json.dumps(kpis, indent=2), encoding="utf-8")
    return {
        "revenue": kpis["revenue"],
        "orders": orders,
        "aov": aov,
        "growth_pct": growth,
        "top_product": kpis["top_product"],
        "top_region": kpis["top_region"],
        "chart": str(base / "revenue_trend.png"),
    }


def demo(base_dir="artifacts"):
    summary = run(quick=True, base_dir=base_dir)
    print(f"Revenue: {summary['revenue']:.2f} from {summary['orders']} orders")
    print(f"Average order value: {summary['aov']:.2f}, growth: {summary['growth_pct']:.1f}%")
    print(f"Top product: {summary['top_product']}, top region: {summary['top_region']}")
