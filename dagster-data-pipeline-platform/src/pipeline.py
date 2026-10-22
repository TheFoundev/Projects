"""A small asset graph with a materialisation log.

The assets depend on each other, the log says which asset depends on which,
and the customers are grouped with the RFM model: how recently they bought,
how often they buy and how much they are worth.
"""
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

#: The assets of the pipeline and the assets they need.
ASSET_GRAPH = {
    "raw_customers": [],
    "clean_customers": ["raw_customers"],
    "customer_segments": ["clean_customers"],
    "segment_report": ["customer_segments"],
}

#: The assets, in the order they are materialised.
ASSETS = list(ASSET_GRAPH)

#: The score of every RFM group: the number of the group and its share.
RFM_GROUPS = {
    "champion": (1, 0),
    "loyal": (2, 1),
    "potential": (3, 2),
    "at_risk": (4, 3),
    "lost": (5, 4),
}


def make_customers(count=120, seed=42):
    rng = np.random.default_rng(seed)
    countries = np.array(["CA", "US", "UK", "DE", "FR", "unknown"])
    frame = pd.DataFrame({
        "customer_id": np.arange(1, count + 1),
        "country": rng.choice(countries, count, p=[0.35, 0.25, 0.15, 0.1, 0.1, 0.05]),
        "signup_date": pd.Timestamp("2025-01-01") + pd.to_timedelta(rng.integers(0, 420, count), unit="D"),
        "monthly_spend": np.round(rng.gamma(2.2, 24, count), 2),
        "orders_last_year": rng.integers(1, 18, count),
        "churned": rng.choice([0, 1], count, p=[0.78, 0.22]),
    })
    # Add a couple of duplicate rows so the clean asset has work to do.
    return pd.concat([frame, frame.iloc[:2]], ignore_index=True)


def rfm_segment(clean, today=None):
    """The RFM group of every customer.

    The recency is the number of days since the customer signed up, the
    frequency is the number of orders and the monetary value is what they
    spend in a year. Every one of the three is scored from one to five by
    its fifth, and the three scores are put together into the groups of the
    model.
    """
    today = today or pd.Timestamp("2026-04-01")
    frame = clean.copy()
    frame["recency"] = (pd.Timestamp(today) - pd.to_datetime(frame["signup_date"])).dt.days
    frame["frequency"] = frame["orders_last_year"]
    frame["monetary"] = frame["monthly_spend"] * 12

    frame["r_score"] = _quintile(frame["recency"], ascending=False)
    frame["f_score"] = _quintile(frame["frequency"], ascending=True)
    frame["m_score"] = _quintile(frame["monetary"], ascending=True)

    def group(row):
        r, f, m = row["r_score"], row["f_score"], row["m_score"]
        if r >= 4 and f >= 4 and m >= 4:
            return "champion"
        if f >= 3 and m >= 3:
            return "loyal"
        if r >= 4:
            return "potential"
        if r <= 2 and f >= 3:
            return "at_risk"
        return "lost"

    frame["rfm_group"] = frame.apply(group, axis=1)
    return frame


def _quintile(series, ascending=True):
    """The score of every value, from one to five, by its fifth."""
    ranked = series.rank(ascending=ascending, method="dense")
    try:
        groups = pd.qcut(ranked, 5, labels=False, duplicates="drop")
        return pd.Series(groups, index=series.index).fillna(1).astype(int) + 1
    except ValueError:
        # There are fewer values than fifths, so everybody gets the same.
        return pd.Series([3] * len(series), index=series.index)


def run(quick=False, base_dir="artifacts"):
    """Materialise every asset and write the lineage."""
    base = Path(base_dir)
    base.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(base / "lineage.db")
    connection.execute(
        "CREATE TABLE IF NOT EXISTS materializations ("
        "asset TEXT, run_id TEXT, upstream TEXT, rows INTEGER, materialized_at TEXT)"
    )
    connection.commit()

    run_id = uuid.uuid4().hex[:12]
    raw = make_customers(60 if quick else 220)
    clean = (
        raw.drop_duplicates(subset=["customer_id"])
        .assign(country=lambda frame: frame["country"].replace("unknown", "Other"))
        .dropna(subset=["customer_id", "monthly_spend"])
    )
    clean["annual_value"] = (clean["monthly_spend"] * 12).round(2)

    segmented = rfm_segment(clean)
    clean = segmented

    report = (
        clean.groupby("rfm_group")
        .agg(customers=("customer_id", "count"),
             avg_annual_value=("annual_value", "mean"),
             churn_rate=("churned", "mean"))
        .reset_index()
        .round(2)
    )

    outputs = {
        "raw_customers": raw,
        "clean_customers": clean,
        "customer_segments": clean[["customer_id", "country", "annual_value",
                                   "orders_last_year", "recency", "frequency",
                                   "monetary", "rfm_group"]],
        "segment_report": report,
    }

    for asset in ASSETS:
        frame = outputs[asset]
        task_dir = base / "warehouse"
        task_dir.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(task_dir / f"{asset}.parquet", index=False)
        connection.execute(
            "INSERT INTO materializations VALUES (?, ?, ?, ?, ?)",
            (asset, run_id, ",".join(ASSET_GRAPH[asset]), len(frame),
             datetime.now(timezone.utc).isoformat(timespec="seconds")),
        )
        connection.commit()
    connection.close()

    return {
        "assets": len(ASSETS),
        "run_id": run_id,
        "customers": int(report["customers"].sum()),
        "segments": int(len(report)),
        "high_value_customers": int(
            report.loc[report["rfm_group"] == "champion", "customers"].sum()
        ),
        "warehouse": str(base / "warehouse"),
    }


def demo(base_dir="artifacts"):
    summary = run(quick=True, base_dir=base_dir)
    report = pd.read_parquet(Path(base_dir) / "warehouse" / "segment_report.parquet")
    print("Asset order:", " -> ".join(ASSETS))
    print(report.to_string(index=False))
    print(
        f"Materialised {summary['assets']} assets for {summary['customers']} customers "
        f"(run {summary['run_id']})."
    )
