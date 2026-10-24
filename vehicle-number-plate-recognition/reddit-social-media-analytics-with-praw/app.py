"""The dashboard of the subreddit analytics and the site of the project.

The posts and the comments are synthetic, so the analytics run without a
Reddit account. The site of the project lives in `web/`, and `/api/summary`
answers with the numbers of the database the pipeline wrote.
"""
import os
import sqlite3
from pathlib import Path

from flask import Flask, jsonify, render_template_string, send_file, send_from_directory

from src.pipeline import run

app = Flask(__name__)
run(quick=True, base_dir="artifacts")

#: The site of the project.
WEB = Path(__file__).resolve().parent / "web"

#: The database the pipeline writes.
DB_PATH = Path("artifacts/analytics.db")

PAGE = """
<!doctype html>
<title>Subreddit analytics</title>
<link rel="stylesheet" href="/assets/theme.css">
<style>
 body { font-family: system-ui, sans-serif; max-width: 820px; margin: 36px auto; color: #1f2937; }
 table { border-collapse: collapse; width: 100%; margin: 16px 0; }
 th, td { text-align: left; padding: 7px 9px; border-bottom: 1px solid #e5e7eb; }
 img { max-width: 100%; border: 1px solid #e5e7eb; }
</style>
<h1>Subreddit analytics</h1>
<p>Posts and comments are synthetic; there is no Reddit API call.</p>
<h2>Activity</h2>
<img src="/chart" alt="Posting activity by hour">
<h2>Top subreddits</h2>
<table>
<tr><th>Subreddit</th><th>Posts</th><th>Score</th><th>Comments</th></tr>
{% for row in rows %}
<tr><td>{{ row[0] }}</td><td>{{ row[1] }}</td><td>{{ row[2] }}</td><td>{{ row[3] }}</td></tr>
{% endfor %}
</table>
<h2>Top posts</h2>
<ul>
{% for row in posts %}
<li><strong>{{ row[0] }}</strong> — score {{ row[1] }}, {{ row[2] }} comments</li>
{% endfor %}
</ul>
<p><a href="/console.html">Open the console</a></p>
"""


def _query(sql: str, parameters: tuple = ()) -> list[tuple]:
    """The rows of a query of the analytics database."""
    if not DB_PATH.exists():
        return []
    connection = sqlite3.connect(DB_PATH)
    try:
        return connection.execute(sql, parameters).fetchall()
    finally:
        connection.close()


def summary_payload():
    """The state of the analytics: the database the pipeline wrote.

    The engagement of a post is its score plus twice its number of
    comments, the same way the pipeline weighs it.
    """
    subreddits = _query(
        "SELECT subreddit, COUNT(*), SUM(score), SUM(comments), "
        "SUM(score + 2 * comments) FROM posts GROUP BY subreddit "
        "ORDER BY SUM(score + 2 * comments) DESC"
    )
    posts = _query("SELECT title, subreddit, score, comments, sentiment_label FROM posts "
                   "ORDER BY score DESC LIMIT 8")
    authors = _query("SELECT author, COUNT(*), SUM(score + 2 * comments) FROM posts "
                     "GROUP BY author ORDER BY SUM(score + 2 * comments) DESC LIMIT 8")
    hours = _query("SELECT hour, COUNT(*), SUM(score + 2 * comments) FROM posts "
                   "GROUP BY hour ORDER BY hour")
    comment_row = _query("SELECT COUNT(*), AVG(sentiment) FROM comments")
    comments = comment_row[0] if comment_row else (0, 0.0)
    runs = _query("SELECT run_at, source, COUNT(*) FROM posts GROUP BY run_at, source "
                  "ORDER BY run_at DESC LIMIT 8")
    total_posts = _query("SELECT COUNT(*) FROM posts")[0][0]
    sentiment = _query("SELECT sentiment_label, COUNT(*) FROM posts GROUP BY sentiment_label")

    return {
        "stats": {
            "posts": int(total_posts),
            "comments": int(comments[0]),
            "subreddits": len(subreddits),
            "positive_share": round(
                float(sum(count for label, count in sentiment if label == "positive"))
                / max(1, total_posts), 4),
        },
        "series": [{"label": f"{int(hour):02d}:00", "value": int(count)} for hour, count, _ in hours],
        "lists": {
            "subreddits": [
                {"subreddit": name, "posts": int(posts_count), "score": int(score or 0),
                 "comments": int(comment_count or 0), "engagement": int(engagement or 0)}
                for name, posts_count, score, comment_count, engagement in subreddits
            ],
            "top_posts": [
                {"title": title, "subreddit": subreddit, "score": int(score),
                 "comments": int(comment_count), "sentiment": label}
                for title, subreddit, score, comment_count, label in posts
            ],
            "authors": [
                {"author": author, "posts": int(count), "engagement": int(engagement or 0)}
                for author, count, engagement in authors
            ],
            "runs": [
                {"run_at": run_at, "source": source, "posts": int(count)}
                for run_at, source, count in runs
            ],
        },
    }


@app.route("/")
def index():
    """The home page of the site of the project."""
    return site_file("index.html")


@app.route("/demo")
def demo():
    """The dashboard of the project, the one that was there before."""
    rows = _query(
        "SELECT subreddit, COUNT(*), SUM(score), SUM(comments) FROM posts GROUP BY subreddit "
        "ORDER BY SUM(score + comments) DESC"
    )
    posts = _query(
        "SELECT title, score, comments FROM posts ORDER BY score DESC LIMIT 5"
    )
    return render_template_string(PAGE, rows=rows, posts=posts)


@app.route("/console.html")
def console():
    return site_file("console.html")


@app.route("/login.html")
def login():
    return site_file("login.html")


@app.route("/assets/<path:name>")
def assets(name):
    """The theme and the runtime of the site."""
    return send_from_directory(WEB / "assets", name)


def site_file(name: str):
    """A page of the site, or the dashboard when the site is not built yet."""
    if not (WEB / name).exists():
        return demo()
    return send_from_directory(WEB, name)


@app.route("/api/summary")
def api_summary():
    """The numbers of the analytics database."""
    return jsonify(summary_payload())


@app.route("/api/subreddits")
def api_subreddits():
    """The engagement of every subreddit."""
    rows = _query(
        "SELECT subreddit, COUNT(*), SUM(score), SUM(comments) FROM posts GROUP BY subreddit "
        "ORDER BY SUM(score + comments) DESC"
    )
    return jsonify({"subreddits": [
        {"subreddit": name, "posts": int(count), "score": int(score or 0),
         "comments": int(comments or 0)} for name, count, score, comments in rows
    ]})


@app.route("/api/history")
def api_history():
    """The runs of the analytics, newest first."""
    rows = _query("SELECT run_at, source, COUNT(*) FROM posts GROUP BY run_at, source "
                  "ORDER BY run_at DESC LIMIT 20")
    return jsonify({"runs": [
        {"run_at": run_at, "source": source, "posts": int(count)} for run_at, source, count in rows
    ]})


@app.route("/chart")
def chart():
    return send_file(Path("artifacts/activity.png"), mimetype="image/png")


if __name__ == "__main__":
    app.run(debug=True, host=os.environ.get("REDDIT_HOST", "127.0.0.1"),
            port=int(os.environ.get("REDDIT_PORT", os.environ.get("PORT", "5000"))))
