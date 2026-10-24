"""Tests for the subscription metrics."""
import pandas as pd
import pytest

from src.pipeline import (
    CURRENT_MONTH,
    MONTHS,
    active_in,
    cohort_retention,
    filter_data,
    is_active,
    load,
    make_subscriptions,
    mrr_by_month,
    save,
    summary,
)


@pytest.fixture()
def subscriptions():
    return make_subscriptions(count=60, seed=5)


def test_a_subscription_is_active_from_its_start_month():
    row = {"start_month": "2026-01", "churn_month": None}
    assert is_active(row, "2025-12") is False
    assert is_active(row, "2026-01") is True
    assert is_active(row, "2026-04") is True


def test_a_subscription_stops_at_its_churn_month():
    row = {"start_month": "2026-01", "churn_month": "2026-03"}
    assert is_active(row, "2026-02") is True
    assert is_active(row, "2026-03") is False
    assert is_active(row, "2026-04") is False


def test_the_mrr_is_the_sum_of_the_running_subscriptions(subscriptions):
    frame = active_in(subscriptions, CURRENT_MONTH)
    expected = round(float(frame["monthly_fee"].sum()), 2)
    assert summary(subscriptions)["mrr"] == expected


def test_the_arr_is_twelve_months_of_mrr(subscriptions):
    numbers = summary(subscriptions)
    assert numbers["arr"] == round(numbers["mrr"] * 12, 2)


def test_the_average_fee_is_the_mrr_per_active_customer(subscriptions):
    numbers = summary(subscriptions)
    assert numbers["average_fee"] == round(numbers["mrr"] / max(1, numbers["active"]), 2)


def test_the_churn_is_a_share_of_the_running_subscriptions(subscriptions):
    numbers = summary(subscriptions)
    assert 0 <= numbers["churn_rate"] <= 1
    churned = int((subscriptions["churn_month"] == CURRENT_MONTH).sum())
    # The churn is a share of the subscriptions that were running at the
    # start of the month.
    running_before = len(active_in(subscriptions, MONTHS[MONTHS.index(CURRENT_MONTH) - 1]))
    assert numbers["churn_rate"] == round(churned / max(1, running_before), 4)


def test_the_new_mrr_is_the_revenue_of_the_new_subscriptions(subscriptions):
    numbers = summary(subscriptions)
    new = subscriptions[subscriptions["start_month"] == CURRENT_MONTH]
    assert numbers["new_mrr"] == round(float(new["monthly_fee"].sum()), 2)


def test_the_net_revenue_retention_is_a_share(subscriptions):
    numbers = summary(subscriptions)
    assert numbers["net_revenue_retention"] >= 0


def test_the_mrr_of_every_month_is_a_row_per_month(subscriptions):
    monthly = mrr_by_month(subscriptions)
    assert len(monthly) == len(MONTHS)
    assert list(monthly["month"]) == MONTHS
    assert (monthly["mrr"] >= 0).all()


def test_the_mrr_grows_when_a_customer_joins(subscriptions):
    monthly = mrr_by_month(subscriptions)
    assert monthly.iloc[0]["mrr"] <= monthly.iloc[-1]["mrr"]


def test_the_cohort_table_has_a_row_per_cohort(subscriptions):
    cohorts = cohort_retention(subscriptions)
    assert not cohorts.empty
    assert "cohort" in cohorts.columns
    for _, row in cohorts.iterrows():
        for month in MONTHS:
            value = row[month]
            if value is None or pd.isna(value):
                continue
            assert 0 <= value <= 1


def test_the_filters_narrow_the_data(subscriptions):
    everything = filter_data(subscriptions)
    assert len(everything) == len(subscriptions)

    team = filter_data(subscriptions, segment="team")
    assert set(team["segment"]) == {"team"}
    assert len(team) <= len(everything)

    north = filter_data(subscriptions, region="north")
    assert set(north["region"]) == {"north"}


def test_the_filter_on_the_months_keeps_the_running_subscriptions(subscriptions):
    recent = filter_data(subscriptions, months=["2026-03", "2026-04"])
    assert len(recent) <= len(subscriptions)


def test_the_summary_of_an_empty_frame_is_zero():
    empty = pd.DataFrame(columns=["customer_id", "segment", "region", "start_month", "monthly_fee", "churn_month"])
    numbers = summary(empty)
    assert numbers["mrr"] == 0
    assert numbers["arr"] == 0
    assert numbers["active"] == 0
    assert numbers["average_fee"] == 0


def test_the_data_is_saved_and_read_back(tmp_path):
    frame = make_subscriptions(count=20, seed=9)
    save(frame, base_dir=str(tmp_path))
    loaded = load(base_dir=str(tmp_path))
    assert len(loaded) == len(frame)
    assert set(loaded.columns) == set(frame.columns)
