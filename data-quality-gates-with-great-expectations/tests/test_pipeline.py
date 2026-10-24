"""Tests for the quality checks."""
import json

import pandas as pd

from src.pipeline import (
    AGE_RANGE,
    VALID_STATUSES,
    Between,
    Check,
    InSet,
    Matches,
    NotNull,
    Unique,
    default_checks,
    make_customers,
    run,
    run_checks,
    demo,
)


def test_pipeline_runs(tmp_path, capsys):
    summary = run(quick=True, base_dir=str(tmp_path))
    assert isinstance(summary, dict)
    assert summary
    assert any(tmp_path.iterdir())

    demo(base_dir=str(tmp_path))
    assert capsys.readouterr().out.strip()


# ---------------------------------------------------------------------------
# The checks
# ---------------------------------------------------------------------------

def test_a_check_that_is_not_written_is_an_error():
    check = Check("empty", "critical")
    try:
        check.evaluate(pd.DataFrame({"a": [1]}))
    except NotImplementedError:
        return
    raise AssertionError("a check without an implementation should raise")


def test_a_missing_value_is_found():
    frame = pd.DataFrame({"customer_id": [1, None, 3]})
    failed = NotNull("customer_id").evaluate(frame)
    assert len(failed) == 1
    assert "reason" in failed.columns


def test_a_duplicated_value_is_found():
    frame = pd.DataFrame({"customer_id": [1, 1, 2]})
    assert len(Unique("customer_id").evaluate(frame)) == 2


def test_a_value_outside_the_range_is_found():
    frame = pd.DataFrame({"age": [20, 13, 100]})
    failed = Between("age", AGE_RANGE[0], AGE_RANGE[1]).evaluate(frame)
    assert len(failed) == 2


def test_a_value_outside_the_set_is_found():
    frame = pd.DataFrame({"status": ["active", "unknown"]})
    failed = InSet("status", VALID_STATUSES).evaluate(frame)
    assert len(failed) == 1
    assert failed.iloc[0]["reason"]


def test_a_value_that_does_not_match_the_pattern_is_found():
    import re

    frame = pd.DataFrame({"email": ["a@b.test", "broken", None]})
    failed = Matches("email", re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")).evaluate(frame)
    assert len(failed) == 2


def test_a_column_that_is_not_there_is_not_a_failure():
    frame = pd.DataFrame({"other": [1, 2]})
    assert len(NotNull("missing").evaluate(frame)) == 0


# ---------------------------------------------------------------------------
# The report
# ---------------------------------------------------------------------------

def test_the_report_names_the_rows_that_failed(tmp_path):
    run(quick=True, base_dir=str(tmp_path))
    report = json.loads((tmp_path / "quality_report.json").read_text())

    assert report["failed_rows"]
    for row in report["failed_rows"]:
        assert row["checks"]
        assert "customer_id" in row


def test_the_report_holds_the_examples_of_a_check(tmp_path):
    run(quick=True, base_dir=str(tmp_path))
    report = json.loads((tmp_path / "quality_report.json").read_text())

    email = next(check for check in report["checks"] if check["name"] == "email_format")
    assert email["failures"] >= 1
    assert email["examples"]


def test_the_severities_are_counted_separately(tmp_path):
    summary = run(quick=True, base_dir=str(tmp_path))
    report = json.loads((tmp_path / "quality_report.json").read_text())

    critical = [c for c in report["checks"] if c["severity"] == "critical"]
    warning = [c for c in report["checks"] if c["severity"] == "warning"]
    assert critical
    assert warning
    assert summary["critical_failures"] == sum(c["failures"] for c in critical)
    assert summary["warning_failures"] == sum(c["failures"] for c in warning)


def test_the_cleaned_table_does_not_hold_the_rows_that_failed_critically(tmp_path):
    run(quick=True, base_dir=str(tmp_path))
    raw = pd.read_csv(tmp_path / "customer_raw.csv")
    clean = pd.read_csv(tmp_path / "customer_clean.csv")

    assert len(clean) < len(raw)
    # The row with the broken email is gone.
    assert "broken-email" not in clean["email"].tolist()


def test_the_cleaning_comes_from_the_checks():
    """The report and the cleaned table may not disagree."""
    frame = make_customers(40, seed=2)
    checks = default_checks()
    results, failures = run_checks(frame, checks)

    critical_rows = set()
    for check in checks:
        if check.severity == "critical":
            critical_rows.update(check.evaluate(frame).index)

    assert set(failures) >= critical_rows
    assert len(frame) - len(critical_rows) == len(frame.drop(index=sorted(critical_rows)))
