"""The subscription analytics page.

Run it with `streamlit run app.py`.
"""
from pathlib import Path

import pandas as pd
import streamlit as st

from src.pipeline import (
    CURRENT_MONTH,
    MONTHS,
    REGIONS,
    SEGMENTS,
    cohort_retention,
    filter_data,
    load,
    mrr_by_month,
    summary,
)

st.set_page_config(page_title="Subscription analytics", layout="wide")

DATA_DIR = Path(__file__).parent / "artifacts"


@st.cache_data(ttl=300)
def read_subscriptions(data_dir: str) -> pd.DataFrame:
    """The subscriptions, cached so the page is quick."""
    return load(data_dir)


st.title("Subscription analytics")
st.caption(
    "The MRR is the monthly fee of the subscriptions that are running in the month. "
    "The average fee is the MRR of the month divided by the number of active "
    "subscriptions, the churn is the share of the running subscriptions that "
    "ended in the month, and the net revenue retention says how much the "
    "customers that were already there brought in."
)

frame = read_subscriptions(str(DATA_DIR))

with st.sidebar:
    st.header("Filters")
    segment = st.selectbox("Segment", ["all"] + SEGMENTS)
    region = st.selectbox("Region", ["all"] + REGIONS)
    first = st.selectbox("From", MONTHS, index=0)
    last = st.selectbox("To", MONTHS, index=len(MONTHS) - 1)
    months = [month for month in MONTHS if MONTHS.index(month) >= MONTHS.index(first)
              and MONTHS.index(month) <= MONTHS.index(last)]
    st.divider()
    st.caption(f"{len(frame)} subscriptions in total")

filtered = filter_data(frame, segment, region, months)
numbers = summary(filtered, CURRENT_MONTH)

columns = st.columns(5)
columns[0].metric("MRR", f"{numbers['mrr']:,.2f}")
columns[1].metric("ARR", f"{numbers['arr']:,.2f}")
columns[2].metric("Active customers", numbers["active"])
columns[3].metric("Average fee", f"{numbers['average_fee']:,.2f}")
columns[4].metric("Churn", f"{numbers['churn_rate'] * 100:.1f}%")

left, right = st.columns(2)

with left:
    st.subheader("The revenue of every month")
    monthly = mrr_by_month(filtered, MONTHS)
    chart = monthly.set_index("month")[["mrr", "customers"]]
    st.line_chart(chart)

with right:
    st.subheader("The revenue by segment")
    if numbers["by_segment"]:
        st.bar_chart(pd.DataFrame(numbers["by_segment"]).set_index("segment")["mrr"])
    else:
        st.info("No subscription matches the filters.")

st.subheader("New customers, churned customers and the revenue of every month")
st.dataframe(
    monthly.rename(columns={
        "mrr": "MRR", "customers": "active", "new": "new", "churned": "churned",
    }),
    use_container_width=True,
)

st.subheader("How much of every cohort is still there")
cohorts = cohort_retention(filtered, MONTHS)
if not cohorts.empty:
    st.dataframe(cohorts.set_index("cohort"), use_container_width=True)
else:
    st.info("No cohort matches the filters.")

st.subheader("The customers")
st.dataframe(filtered.sort_values("monthly_fee", ascending=False), use_container_width=True)

st.download_button(
    "Download the subscriptions",
    filtered.to_csv(index=False).encode("utf-8"),
    file_name="subscriptions.csv",
    mime="text/csv",
)
