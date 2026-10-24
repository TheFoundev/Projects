"""Quality checks plus a cleaned customer table.

Every check is written down once: the check says what it looks at and how
severe it is, and both the number of the failures and the cleaning of the
table come from it, so the report and the output can never disagree.
"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = ["customer_id", "email", "age", "status", "country"]

#: The statuses a customer may have.
VALID_STATUSES = ["active", "paused", "cancelled"]

#: The age a customer has to be in.
AGE_RANGE = (18, 90)

#: The countries the customers come from.
VALID_COUNTRIES = ["CA", "US", "UK", "DE"]

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Check:
    """One quality check.

    The check knows what it looks at and how bad it is when it fails, so the
    number of the failures and the rows that are thrown away are both worked
    out from it.
    """

    def __init__(self, name, severity, description=""):
        self.name = name
        self.severity = severity
        self.description = description

    def evaluate(self, frame):
        """The rows that fail the check, with the reason."""
        raise NotImplementedError


class ColumnPresent(Check):
    """The column has to be there."""

    def __init__(self, column, severity="critical"):
        super().__init__(f"{column}_present", severity, f"the column {column} has to be there")
        self.column = column

    def evaluate(self, frame):
        if self.column in frame.columns:
            return frame.iloc[0:0].assign(reason="")
        return frame.iloc[0:0].assign(reason=f"the column {self.column} is missing")


class NotNull(Check):
    """The value may not be missing."""

    def __init__(self, column, severity="critical"):
        super().__init__(f"{column}_not_null", severity, f"the column {column} may not be empty")
        self.column = column

    def evaluate(self, frame):
        if self.column not in frame.columns:
            return frame.iloc[0:0].assign(reason="")
        failed = frame[frame[self.column].isna()].copy()
        failed["reason"] = f"{self.column} is empty"
        return failed


class Unique(Check):
    """The value may only be there once."""

    def __init__(self, column, severity="critical"):
        super().__init__(f"{column}_unique", severity, f"the column {column} may only be there once")
        self.column = column

    def evaluate(self, frame):
        if self.column not in frame.columns:
            return frame.iloc[0:0].assign(reason="")
        duplicated = frame[frame.duplicated(subset=[self.column], keep=False)].copy()
        duplicated["reason"] = f"{self.column} is there more than once"
        return duplicated


class Matches(Check):
    """The value has to match a pattern."""

    def __init__(self, column, pattern, severity="critical"):
        super().__init__(f"{column}_format", severity, f"the column {column} has to match {pattern.pattern}")
        self.column = column
        self.pattern = pattern

    def evaluate(self, frame):
        if self.column not in frame.columns:
            return frame.iloc[0:0].assign(reason="")
        values = frame[self.column].fillna("").astype(str)
        failed = frame[~values.str.match(self.pattern)].copy()
        failed["reason"] = f"{self.column} is not a valid value"
        return failed


class Between(Check):
    """The value has to be inside a range."""

    def __init__(self, column, low, high, severity="critical"):
        super().__init__(f"{column}_range", severity, f"the column {column} has to be between {low} and {high}")
        self.column = column
        self.low = low
        self.high = high

    def evaluate(self, frame):
        if self.column not in frame.columns:
            return frame.iloc[0:0].assign(reason="")
        failed = frame[~frame[self.column].between(self.low, self.high)].copy()
        failed["reason"] = f"{self.column} is not between {self.low} and {self.high}"
        return failed


class InSet(Check):
    """The value has to be one of a set."""

    def __init__(self, column, allowed, severity="warning"):
        super().__init__(f"{column}_values", severity, f"the column {column} has to be one of {', '.join(allowed)}")
        self.column = column
        self.allowed = allowed

    def evaluate(self, frame):
        if self.column not in frame.columns:
            return frame.iloc[0:0].assign(reason="")
        failed = frame[~frame[self.column].isin(self.allowed)].copy()
        failed["reason"] = f"{self.column} is not one of the allowed values"
        return failed


#: The checks of the pipeline, with how severe they are.
def default_checks():
    """The checks the pipeline runs."""
    return [
        ColumnPresent("customer_id"),
        NotNull("customer_id"),
        Unique("customer_id"),
        NotNull("email"),
        Matches("email", EMAIL_PATTERN),
        Between("age", AGE_RANGE[0], AGE_RANGE[1]),
        InSet("status", VALID_STATUSES, severity="warning"),
        NotNull("country", severity="warning"),
    ]


def make_customers(count=80, seed=42):
    """A table of customers with a few problems in it."""
    rng = np.random.default_rng(seed)
    frame = pd.DataFrame({
        "customer_id": np.arange(1, count + 3),
        "email": [f"user{index}@example.com" for index in range(1, count + 3)],
        "age": rng.integers(18, 80, count + 2),
        "status": rng.choice(VALID_STATUSES, count + 2),
        "country": rng.choice(VALID_COUNTRIES, count + 2),
    })
    frame.loc[3, "email"] = "broken-email"
    frame.loc[7, "age"] = 13
    frame.loc[11, "status"] = "unknown"
    frame.loc[15, "country"] = None
    frame.loc[17, "email"] = None
    frame = pd.concat([frame, frame.iloc[[4]]], ignore_index=True)
    return frame


def run_checks(frame, checks=None):
    """Run the checks over a table.

    Every check gives the rows that failed it, so the report can name them.
    """
    checks = checks if checks is not None else default_checks()
    results = []
    failures_by_row = {}

    for check in checks:
        failed = check.evaluate(frame)
        results.append({
            "name": check.name,
            "passed": len(failed) == 0,
            "failures": int(len(failed)),
            "severity": check.severity,
            "description": check.description,
            "examples": failed.head(5)[["customer_id", "reason"]].to_dict("records")
            if "customer_id" in failed.columns else [],
        })
        for index in failed.index:
            failures_by_row.setdefault(index, []).append(check.name)

    return results, failures_by_row


def run(quick=False, base_dir="artifacts"):
    """Run the checks, write the report and the cleaned table."""
    base = Path(base_dir)
    base.mkdir(parents=True, exist_ok=True)
    frame = make_customers(48 if quick else 160)
    frame.to_csv(base / "customer_raw.csv", index=False)

    checks = default_checks()
    results, failures_by_row = run_checks(frame, checks)

    critical_failures = sum(check["failures"] for check in results if check["severity"] == "critical")
    warning_failures = sum(check["failures"] for check in results if check["severity"] == "warning")

    # The rows that a critical check threw away do not go into the cleaned
    # table. The rows of a warning stay: they are reported, not hidden.
    critical_checks = [check for check in checks if check.severity == "critical"]
    critical_rows = set()
    for check in critical_checks:
        critical_rows.update(check.evaluate(frame).index)

    clean = frame.drop(index=sorted(critical_rows))
    clean.to_csv(base / "customer_clean.csv", index=False)

    report = {
        "rows": int(len(frame)),
        "clean_rows": int(len(clean)),
        "checks": results,
        "critical_failures": critical_failures,
        "warning_failures": warning_failures,
        "failed_rows": [
            {"customer_id": int(index) if index in frame["customer_id"].values else str(index),
             "checks": names}
            for index, names in sorted(failures_by_row.items())
        ],
        "passed": critical_failures == 0,
    }
    (base / "quality_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    return {
        "rows": report["rows"],
        "clean_rows": report["clean_rows"],
        "checks": len(results),
        "critical_failures": critical_failures,
        "warning_failures": warning_failures,
        "passed": report["passed"],
        "report": str(base / "quality_report.json"),
    }


def demo(base_dir="artifacts"):
    summary = run(quick=True, base_dir=base_dir)
    report = json.loads((Path(base_dir) / "quality_report.json").read_text())
    for check in report["checks"]:
        state = "ok  " if check["passed"] else "FAIL"
        print(f"  {state} {check['name']:24s} {check['failures']:4d} failure(s) [{check['severity']}]")
    print(
        f"{summary['rows']} rows, {summary['clean_rows']} clean, "
        f"{summary['critical_failures']} critical and {summary['warning_failures']} warning failure(s)"
    )
    if report["failed_rows"]:
        print("The rows that failed:")
        for row in report["failed_rows"][:5]:
            print(f"  customer {row['customer_id']}: {', '.join(row['checks'])}")
