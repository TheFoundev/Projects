"""Tests for the asset graph and the RFM grouping."""
import sqlite3

import pandas as pd

from src.pipeline import ASSET_GRAPH, ASSETS, make_customers, rfm_segment, run, demo


def test_pipeline_runs(tmp_path, capsys):
    summary = run(quick=True, base_dir=str(tmp_path))
    assert isinstance(summary, dict)
    assert summary
    assert any(tmp_path.iterdir())

    demo(base_dir=str(tmp_path))
    assert capsys.readouterr().out.strip()


def test_every_asset_has_its_dependencies():
    """The graph says what every asset needs."""
    assert ASSET_GRAPH["raw_customers"] == []
    assert ASSET_GRAPH["clean_customers"] == ["raw_customers"]
    assert ASSET_GRAPH["segment_report"] == ["customer_segments"]
    # The order of the assets follows the graph.
    for asset, needs in ASSET_GRAPH.items():
        for need in needs:
            assert ASSETS.index(need) < ASSETS.index(asset)


def test_the_duplicates_are_removed():
    raw = make_customers(20, seed=1)
    clean = raw.drop_duplicates(subset=["customer_id"])
    assert len(clean) == len(raw) - 2


def test_the_log_says_what_every_asset_depends_on(tmp_path):
    run(quick=True, base_dir=str(tmp_path))
    connection = sqlite3.connect(tmp_path / "lineage.db")
    rows = connection.execute(
        "SELECT asset, run_id, upstream, rows FROM materializations"
    ).fetchall()
    connection.close()

    upstream = {row[0]: row[2] for row in rows}
    assert upstream["raw_customers"] == ""
    assert upstream["clean_customers"] == "raw_customers"
    assert upstream["segment_report"] == "customer_segments"
    assert len({row[1] for row in rows}) == 1, "one run has one id"


def test_the_rfm_groups_are_the_five_of_the_model():
    clean = make_customers(60, seed=2).drop_duplicates(subset=["customer_id"])
    segmented = rfm_segment(clean)
    groups = set(segmented["rfm_group"])

    assert groups
    assert groups <= {"champion", "loyal", "potential", "at_risk", "lost"}
    assert "champion" in groups


def test_the_recency_the_frequency_and_the_monetary_are_there():
    clean = make_customers(40, seed=3).drop_duplicates(subset=["customer_id"])
    segmented = rfm_segment(clean)

    for column in ("recency", "frequency", "monetary", "rfm_group"):
        assert column in segmented.columns
    assert (segmented["recency"] >= 0).all()
    assert (segmented["monetary"] > 0).all()


def test_the_report_counts_the_customers_of_every_group(tmp_path):
    summary = run(quick=True, base_dir=str(tmp_path))
    report = pd.read_parquet(tmp_path / "warehouse" / "segment_report.parquet")

    assert report["customers"].sum() == summary["customers"]
    assert set(report["rfm_group"]) <= {"champion", "loyal", "potential", "at_risk", "lost"}


def test_the_assets_are_written_as_parquet(tmp_path):
    run(quick=True, base_dir=str(tmp_path))
    for asset in ASSETS:
        assert (tmp_path / "warehouse" / f"{asset}.parquet").exists()
