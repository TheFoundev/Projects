"""Collect Reddit posts and comments, then compute the engagement analytics.

The data comes from a `RedditSource`. The project ships with the synthetic
source, so it runs without an account, and `PrawRedditSource` talks to the
real Reddit API when praw and the credentials are there.
"""
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

SUBREDDITS = ["learnpython", "datascience", "webdev", "devops"]
POSITIVE = ["helpful", "great", "clear", "works", "thanks", "nice", "useful", "solved"]
NEGATIVE = ["confusing", "broken", "slow", "error", "stuck", "hate", "wrong", "failed"]

#: How a post is scored. The score of Reddit and the number of comments are
#: not on the same scale, so they are weighted before they are added.
SCORE_WEIGHT = 1.0
COMMENT_WEIGHT = 2.0


# ---------------------------------------------------------------------------
# The sources
# ---------------------------------------------------------------------------


class RedditSource:
    """Where the posts and the comments come from."""

    name = "base"

    def fetch(self, limit=120):
        """Return the posts and the comments as two data frames."""
        raise NotImplementedError


class SyntheticRedditSource(RedditSource):
    """A generator that makes Reddit-style posts and comments."""

    name = "synthetic"

    def __init__(self, seed=42):
        self.seed = seed

    def fetch(self, limit=120):
        rng = np.random.default_rng(self.seed)
        titles = [
            "How do I structure a small project?",
            "My first dashboard finally works",
            "Question about testing database code",
            "A short note on deployment",
            "Why is this query slow?",
            "Sharing a weekend side project",
        ]
        posts = []
        for index in range(limit):
            words = rng.choice(POSITIVE + NEGATIVE, size=5)
            body = " ".join(words) + " " + str(rng.choice(titles))
            posts.append({
                "post_id": index + 1,
                "subreddit": str(rng.choice(SUBREDDITS)),
                "title": str(rng.choice(titles)),
                "body": body,
                "score": int(rng.integers(0, 220)),
                "comments": int(rng.integers(0, 40)),
                "hour": int(rng.integers(0, 24)),
                "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "author": f"user_{index % 17}",
            })
        posts = pd.DataFrame(posts)

        comment_rows = []
        for index in range(limit * 2):
            text = " ".join(rng.choice(POSITIVE + NEGATIVE, size=4))
            comment_rows.append({
                "comment_id": index + 1,
                "post_id": int(rng.integers(1, limit + 1)),
                "body": text,
                "score": int(rng.integers(-2, 40)),
                "author": f"user_{index % 23}",
                "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            })
        return posts, pd.DataFrame(comment_rows)


class PrawRedditSource(RedditSource):
    """The real Reddit API, through praw.

    The credentials come from the environment: REDDIT_CLIENT_ID,
    REDDIT_CLIENT_SECRET and REDDIT_USER_AGENT. Nothing is written to disk.
    """

    name = "praw"

    def __init__(self, subreddits=None, sort="top", time_filter="week"):
        self.subreddits = subreddits or SUBREDDITS
        self.sort = sort
        self.time_filter = time_filter

    def fetch(self, limit=120):
        import praw  # imported here so the project runs without it

        reddit = praw.Reddit(
            client_id=os.environ.get("REDDIT_CLIENT_ID"),
            client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
            user_agent=os.environ.get("REDDIT_USER_AGENT", "foundev-reddit-analytics"),
        )

        posts = []
        comments = []
        post_id = 0
        comment_id = 0

        for subreddit in self.subreddits:
            listing = reddit.subreddit(subreddit).top(limit=limit, time_filter=self.time_filter)
            for submission in listing:
                post_id += 1
                posts.append({
                    "post_id": post_id,
                    "subreddit": subreddit,
                    "title": submission.title,
                    "body": (submission.selftext or "")[:4000],
                    "score": submission.score,
                    "comments": submission.num_comments,
                    "hour": submission.created_utc and datetime.fromtimestamp(
                        submission.created_utc, tz=timezone.utc
                    ).hour,
                    "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "author": str(submission.author),
                })
                try:
                    submission.comments_ = list(submission.comments)
                except Exception:
                    submission.comments_ = []
                for comment in submission.comments_:
                    if not hasattr(comment, "body"):
                        continue
                    comment_id += 1
                    comments.append({
                        "comment_id": comment_id,
                        "post_id": post_id,
                        "body": comment.body[:4000],
                        "score": comment.score,
                        "author": str(comment.author),
                        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    })

        return pd.DataFrame(posts), pd.DataFrame(comments)


# ---------------------------------------------------------------------------
# The sentiment
# ---------------------------------------------------------------------------

_analyzer = None


def _vader():
    """The sentiment analyser, made when it is first needed."""
    global _analyzer
    if _analyzer is None:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

        _analyzer = SentimentIntensityAnalyzer()
    return _analyzer


def sentiment(text):
    """The sentiment of a text, between -1 and 1.

    The compound score of VADER is used, so a negation ("not good") is
    understood and the punctuation and the capital letters count.
    """
    if not str(text).strip():
        return 0.0
    try:
        return round(float(_vader().polarity_scores(str(text))["compound"]), 4)
    except Exception:
        # Without the analyser the lexicon of the generator is used, so the
        # pipeline still works.
        return float(sentiment_from_lexicon(text))


def sentiment_from_lexicon(text):
    """The sentiment of a text with the small lexicon of the generator."""
    words = str(text).lower().split()
    positive = sum(word in POSITIVE for word in words)
    negative = sum(word in NEGATIVE for word in words)
    if positive == negative:
        return 0.0
    return 1.0 if positive > negative else -1.0


def sentiment_label(score):
    """The label of a sentiment score."""
    if score >= 0.05:
        return "positive"
    if score <= -0.05:
        return "negative"
    return "neutral"


# ---------------------------------------------------------------------------
# The analytics
# ---------------------------------------------------------------------------


def engagement(post):
    """The engagement of a post.

    The score of the post and the number of comments are added, with the
    comments counting double because a reply is more work for the author
    than a point is.
    """
    return SCORE_WEIGHT * float(post["score"]) + COMMENT_WEIGHT * float(post["comments"])


def by_subreddit(posts):
    """The engagement of every subreddit, with the averages."""
    frame = posts.copy()
    frame["engagement"] = frame.apply(engagement, axis=1)
    grouped = frame.groupby("subreddit").agg(
        posts=("post_id", "count"),
        score=("score", "sum"),
        comments=("comments", "sum"),
        engagement=("engagement", "sum"),
    )
    grouped["average_engagement"] = grouped["engagement"] / grouped["posts"]
    grouped["average_score"] = grouped["score"] / grouped["posts"]
    return grouped.sort_values("engagement", ascending=False).reset_index()


def by_hour(posts):
    """The number of posts per hour of the day."""
    return posts.groupby("hour").agg(posts=("post_id", "count"), engagement=("score", "sum")).reset_index()


def comment_analysis(comments, posts):
    """What the comments say and who writes them."""
    if comments is None or len(comments) == 0:
        return {"comments": 0, "positive_share": 0.0, "top_commenters": [], "thread_depth": {}}

    frame = comments.copy()
    frame["sentiment"] = frame["body"].map(sentiment)

    top = (
        frame.groupby("author")
        .agg(comments=("comment_id", "count"), score=("score", "sum"))
        .sort_values("comments", ascending=False)
        .head(5)
        .reset_index()
    )

    depth = {}
    if "post_id" in frame.columns:
        depth = {str(key): int(value) for key, value in frame.groupby("post_id").size().items()}

    return {
        "comments": int(len(frame)),
        "positive_share": round(float((frame["sentiment"] > 0.05).mean()), 4),
        "negative_share": round(float((frame["sentiment"] < -0.05).mean()), 4),
        "top_commenters": top.to_dict("records"),
        "thread_depth": depth,
    }


def author_analysis(posts):
    """How much every author posts and how much the posts are read."""
    if "author" not in posts.columns:
        return []
    frame = posts.copy()
    frame["engagement"] = frame.apply(engagement, axis=1)
    grouped = frame.groupby("author").agg(
        posts=("post_id", "count"), engagement=("engagement", "sum")
    )
    grouped = grouped.sort_values("engagement", ascending=False).reset_index()
    return grouped.to_dict("records")


def _prepare_table(connection, name, frame):
    """Make sure the table holds the columns of the frame.

    A database of an older version may hold a table with fewer columns. The
    rows of such a table cannot be read back with the current columns, so the
    table is replaced instead of breaking the run.
    """
    existing = [row[1] for row in connection.execute(f"PRAGMA table_info({name})")]
    if existing and existing != list(frame.columns):
        connection.execute(f"DROP TABLE {name}")


def store_posts(connection, posts, comments, source="synthetic"):
    """Write the posts and the comments to the database.

    The rows are appended, with the time of the run, so the history of the
    runs is kept and the trends can be seen.
    """
    # The time has the microseconds, so two runs in the same second are still
    # two runs.
    run_at = datetime.now(timezone.utc).isoformat(timespec="microseconds")
    posts = posts.copy()
    posts["run_at"] = run_at
    posts["source"] = source
    comments = comments.copy()
    comments["run_at"] = run_at
    comments["source"] = source

    _prepare_table(connection, "posts", posts)
    _prepare_table(connection, "comments", comments)
    posts.to_sql("posts", connection, if_exists="append", index=False)
    comments.to_sql("comments", connection, if_exists="append", index=False)
    connection.commit()
    return run_at


def run(quick=False, base_dir="artifacts", source=None):
    """Collect the data, store it and work out the analytics."""
    base = Path(base_dir)
    base.mkdir(parents=True, exist_ok=True)

    if source is None:
        source = SyntheticRedditSource()
    posts, comments = source.fetch(30 if quick else 120)

    posts["sentiment"] = posts["body"].map(sentiment)
    posts["sentiment_label"] = posts["sentiment"].map(sentiment_label)
    if len(comments) > 0:
        comments["sentiment"] = comments["body"].map(sentiment)

    db_path = base / "analytics.db"
    connection = sqlite3.connect(db_path)
    run_at = store_posts(connection, posts, comments, source.name)

    subreddit = by_subreddit(posts)
    hourly = by_hour(posts)
    connection.close()

    top = subreddit.iloc[0]
    comments_summary = comment_analysis(comments, posts)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(11, 3.2))
    axes[0].plot(hourly["hour"], hourly["posts"], marker="o", color="#2563eb")
    axes[0].set_xlabel("hour of day")
    axes[0].set_ylabel("posts")
    axes[0].set_title("Posting activity by hour")
    axes[0].grid(alpha=0.25)
    axes[1].bar(subreddit["subreddit"], subreddit["engagement"], color="#c2410c")
    axes[1].set_title("Engagement by subreddit")
    axes[1].tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(base / "activity.png", dpi=120)
    plt.close(fig)

    return {
        "posts": int(len(posts)),
        "comments": int(len(comments)),
        "top_subreddit": str(top["subreddit"]),
        "top_engagement": round(float(top["engagement"]), 2),
        "average_engagement": round(float(top["average_engagement"]), 2),
        "positive_share": round(float((posts["sentiment"] > 0.05).mean()), 4),
        "negative_share": round(float((posts["sentiment"] < -0.05).mean()), 4),
        "comment_positive_share": comments_summary["positive_share"],
        "top_commenters": comments_summary["top_commenters"][:3],
        "authors": author_analysis(posts)[:3],
        "source": source.name,
        "run_at": run_at,
        "chart": str(base / "activity.png"),
    }


def history(base_dir="artifacts", limit=20):
    """The runs of the analytics, newest first."""
    db_path = Path(base_dir) / "analytics.db"
    if not db_path.exists():
        return []
    connection = sqlite3.connect(db_path)
    rows = pd.read_sql_query(
        "SELECT run_at, source, COUNT(*) AS posts, SUM(score) AS score, SUM(comments) AS comments "
        "FROM posts GROUP BY run_at, source ORDER BY run_at DESC LIMIT ?",
        connection,
        params=(limit,),
    )
    connection.close()
    return rows.to_dict("records")


def demo(base_dir="artifacts"):
    summary = run(quick=True, base_dir=base_dir)
    connection = sqlite3.connect(Path(base_dir) / "analytics.db")
    print(pd.read_sql_query(
        "SELECT subreddit, COUNT(*) AS posts, SUM(score) AS score, SUM(comments) AS comments "
        "FROM posts GROUP BY subreddit ORDER BY SUM(score + comments) DESC", connection
    ).to_string(index=False))
    print(f"Top subreddit: {summary['top_subreddit']}, positive share: {summary['positive_share']:.2f}")
    print(pd.read_sql_query("SELECT * FROM posts ORDER BY score DESC LIMIT 3", connection).to_string(index=False))
    connection.close()
    print(f"Runs so far: {len(history(base_dir))}")
