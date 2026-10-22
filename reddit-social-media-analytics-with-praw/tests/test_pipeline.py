"""Tests for the Reddit analytics."""
from src.pipeline import (
    PrawRedditSource,
    RedditSource,
    SyntheticRedditSource,
    author_analysis,
    by_hour,
    by_subreddit,
    comment_analysis,
    engagement,
    history,
    run,
    sentiment,
    sentiment_from_lexicon,
    sentiment_label,
)


def test_the_pipeline_runs(tmp_path, capsys):
    summary = run(quick=True, base_dir=str(tmp_path))
    assert isinstance(summary, dict)
    assert summary
    assert any(tmp_path.iterdir())

    from src.pipeline import demo

    demo(base_dir=str(tmp_path))
    assert capsys.readouterr().out.strip()


def test_the_sentiment_understands_a_negation():
    """A negation has to change the sign of the sentiment."""
    assert sentiment("this is great and useful") > 0
    assert sentiment("this is confusing and broken") < 0
    assert sentiment("this is not good at all") < 0
    assert sentiment("") == 0


def test_the_sentiment_has_a_label():
    assert sentiment_label(0.8) == "positive"
    assert sentiment_label(-0.8) == "negative"
    assert sentiment_label(0.0) == "neutral"


def test_the_lexicon_fallback_still_works():
    assert sentiment_from_lexicon("great helpful") == 1.0
    assert sentiment_from_lexicon("confusing broken") == -1.0
    assert sentiment_from_lexicon("hello") == 0.0


def test_the_engagement_is_defined():
    """The engagement is the score plus twice the number of comments."""
    assert engagement({"score": 10, "comments": 3}) == 16.0


def test_the_subreddit_table_has_the_averages(tmp_path):
    summary = run(quick=True, base_dir=str(tmp_path))
    assert summary["top_subreddit"]
    assert summary["top_engagement"] > 0
    assert "average_engagement" in summary


def test_the_comments_are_analysed(tmp_path):
    summary = run(quick=True, base_dir=str(tmp_path))
    assert summary["comments"] > 0
    assert summary["comment_positive_share"] >= 0
    assert summary["top_commenters"]


def test_the_authors_are_ranked(tmp_path):
    summary = run(quick=True, base_dir=str(tmp_path))
    assert summary["authors"]
    first = summary["authors"][0]
    assert "author" in first and "posts" in first


def test_the_runs_are_kept(tmp_path):
    """Two runs leave two rows in the history."""
    run(quick=True, base_dir=str(tmp_path))
    run(quick=True, base_dir=str(tmp_path))
    entries = history(base_dir=str(tmp_path))
    assert len(entries) == 2
    assert entries[0]["posts"] > 0


def test_the_history_is_empty_without_a_database(tmp_path):
    assert history(base_dir=str(tmp_path)) == []


def test_the_source_can_be_swapped(tmp_path):
    """A source is an interface, so the pipeline works with any of them."""
    source = SyntheticRedditSource(seed=3)
    posts, comments = source.fetch(10)
    assert len(posts) == 10
    assert len(comments) == 20

    summary = run(quick=True, base_dir=str(tmp_path), source=source)
    assert summary["source"] == "synthetic"


def test_the_praw_source_needs_the_package():
    """The real source is only usable with praw and the credentials."""
    assert PrawRedditSource().name == "praw"
    assert issubclass(PrawRedditSource, RedditSource)
