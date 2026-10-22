"""Subscription data and the metrics that are worked out from it.

The metrics are defined here, so the numbers on the page mean the same thing
everywhere:

MRR          the monthly fee of the subscriptions that are running in the
             month. It is the sum of the fee of every subscription that has
             started and has not churned yet.
ARR          the MRR of the current month times twelve.
Active       the subscriptions that are running in the current month.
Average fee  the MRR of the month divided by the number of active
             subscriptions (the revenue per customer).
Churn        the subscriptions that ended in the month, as a share of the
             subscriptions that were running at the start of the month.
New MRR      the MRR the new subscriptions of the month brought in.
Expansion    the extra MRR the subscriptions that were already there
             brought in.
Net revenue  the MRR of the subscriptions that were there a year ago, plus
             what they brought since, as a share of what they brought then.
             It is the number that says whether the business grows with the
             customers it already has.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

SEGMENTS = ["student", "starter", "team", "business"]
REGIONS = ["north", "south", "east", "west"]

#: The fee of a plan, before the discount every customer gets.
PLAN_FEE = {"student": 5, "starter": 12, "team": 29, "business": 79}

#: The months the data covers.
MONTHS = ["2025-11", "2025-12", "2026-01", "2026-02", "2026-03", "2026-04"]

#: The month the page is about.
CURRENT_MONTH = "2026-04"


def _month_index(month: str) -> int:
    return MONTHS.index(month)


def make_subscriptions(count=180, seed=21, churn_rate=0.12):
    """A set of subscriptions with a start month and, for some of them, the
    month they churned in."""
    rng = np.random.default_rng(seed)
    plans = rng.choice(SEGMENTS, count, p=[0.3, 0.3, 0.25, 0.15])
    starts = rng.choice(MONTHS[:4], count, p=[0.3, 0.3, 0.2, 0.2])
    fees = np.array([PLAN_FEE[plan] for plan in plans]) * rng.uniform(0.9, 1.2, count)

    frame = pd.DataFrame({
        "customer_id": np.arange(1, count + 1),
        "segment": plans,
        "region": rng.choice(REGIONS, count),
        "start_month": starts,
        "monthly_fee": fees.round(2),
    })

    churned = []
    for start in frame["start_month"]:
        first = _month_index(start)
        room = len(MONTHS) - 1 - first
        if room > 0 and rng.random() < churn_rate:
            churned.append(MONTHS[first + int(rng.integers(1, room + 1))])
        else:
            churned.append(None)
    frame["churn_month"] = churned
    return frame


def is_active(row, month: str) -> bool:
    """True when a subscription is running in a month."""
    if _month_index(row["start_month"]) > _month_index(month):
        return False
    churn = row.get("churn_month")
    if churn is None or (isinstance(churn, float) and np.isnan(churn)):
        return True
    return _month_index(churn) > _month_index(month)


def active_in(frame: pd.DataFrame, month: str) -> pd.DataFrame:
    """The subscriptions that are running in a month."""
    if frame.empty:
        return frame
    mask = frame.apply(lambda row: is_active(row, month), axis=1)
    return frame[mask]


def mrr_by_month(frame: pd.DataFrame, months=None) -> pd.DataFrame:
    """The MRR of every month."""
    months = months or MONTHS
    rows = []
    for month in months:
        active = active_in(frame, month)
        rows.append({
            "month": month,
            "mrr": round(float(active["monthly_fee"].sum()), 2),
            "customers": int(len(active)),
            "new": int((frame["start_month"] == month).sum()),
            "churned": int((frame["churn_month"] == month).sum()),
        })
    return pd.DataFrame(rows)


def summary(frame: pd.DataFrame, month: str = CURRENT_MONTH) -> dict:
    """The numbers the page shows."""
    if frame.empty:
        return {
            "mrr": 0.0, "arr": 0.0, "active": 0, "customers": int(len(frame)),
            "average_fee": 0.0, "churn_rate": 0.0, "new_mrr": 0.0, "net_revenue_retention": 0.0,
            "by_segment": [], "by_region": [],
        }

    active = active_in(frame, month)
    previous_month = MONTHS[max(0, _month_index(month) - 1)]
    previous = active_in(frame, previous_month)

    mrr = float(active["monthly_fee"].sum())
    churned = int((frame["churn_month"] == month).sum())
    churn_rate = churned / max(1, len(previous))

    new = frame[frame["start_month"] == month]
    new_mrr = float(new["monthly_fee"].sum())

    # The customers that were there a year ago would be the ones that started
    # before the first month of the year; with the data of this project that
    # is the first month, so the year-ago revenue is the MRR of that month.
    year_ago_month = MONTHS[0]
    year_ago = active_in(frame, year_ago_month)
    year_ago_ids = set(year_ago["customer_id"])
    kept = frame[frame["customer_id"].isin(year_ago_ids) & (frame["churn_month"].isna()
                                                            | (frame["churn_month"] > year_ago_month))]
    kept_mrr = float(active[active["customer_id"].isin(year_ago_ids)]["monthly_fee"].sum())
    net_revenue_retention = kept_mrr / max(1e-6, float(year_ago["monthly_fee"].sum()))

    by_segment = (
        active.groupby("segment", as_index=False)
        .agg(customers=("customer_id", "count"), mrr=("monthly_fee", "sum"))
        .assign(mrr=lambda frame: frame["mrr"].round(2))
        .sort_values("mrr", ascending=False)
    )
    by_region = (
        active.groupby("region", as_index=False)
        .agg(customers=("customer_id", "count"), mrr=("monthly_fee", "sum"))
        .assign(mrr=lambda frame: frame["mrr"].round(2))
    )

    return {
        "mrr": round(mrr, 2),
        "arr": round(mrr * 12, 2),
        "active": int(len(active)),
        "customers": int(len(frame)),
        "average_fee": round(mrr / max(1, len(active)), 2),
        "churn_rate": round(churn_rate, 4),
        "new_mrr": round(new_mrr, 2),
        "net_revenue_retention": round(net_revenue_retention, 4),
        "by_segment": by_segment.to_dict(orient="records"),
        "by_region": by_region.to_dict(orient="records"),
    }


def cohort_retention(frame: pd.DataFrame, months=None) -> pd.DataFrame:
    """How much of every cohort is still there in every month."""
    months = months or MONTHS
    rows = []
    for cohort in MONTHS:
        group = frame[frame["start_month"] == cohort]
        if group.empty:
            continue
        row = {"cohort": cohort, "customers": int(len(group))}
        for month in months:
            if _month_index(month) < _month_index(cohort):
                row[month] = None
                continue
            kept = active_in(group, month)
            row[month] = round(len(kept) / len(group), 4)
        rows.append(row)
    return pd.DataFrame(rows)


def filter_data(frame: pd.DataFrame, segment=None, region=None, months=None) -> pd.DataFrame:
    """Filter the subscriptions by segment, by region and by the months they
    were running in."""
    result = frame
    if segment and segment != "all":
        result = result[result["segment"] == segment]
    if region and region != "all":
        result = result[result["region"] == region]
    if months:
        first, last = _month_index(months[0]), _month_index(months[-1])
        result = result[
            result.apply(
                lambda row: any(
                    _month_index(month) >= first
                    and _month_index(month) <= last
                    and is_active(row, month)
                    for month in months
                ),
                axis=1,
            )
        ]
    return result


def save(frame: pd.DataFrame, base_dir="artifacts"):
    """Write the subscriptions and the summary to the data directory."""
    base = Path(base_dir)
    base.mkdir(parents=True, exist_ok=True)
    frame.to_csv(base / "subscriptions.csv", index=False)
    (base / "summary.json").write_text(json.dumps(summary(frame), indent=2), encoding="utf-8")
    return str(base)


def load(base_dir="artifacts") -> pd.DataFrame:
    """Read the subscriptions back.

    When there is no file yet, the data is generated, so the app always has
    something to show.
    """
    path = Path(base_dir) / "subscriptions.csv"
    if path.exists():
        return pd.read_csv(path)
    frame = make_subscriptions()
    save(frame, base_dir)
    return frame
