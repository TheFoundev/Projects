# Reddit Social Media Analytics with PRAW

Analyse synthetic subreddit posts and comments in SQLite.

> Collect subreddit posts and comments to track sentiment trends, topic bursts and community engagement over time in a live dashboard.

## Overview

An original, self-contained implementation of the **Reddit Social Media Analytics with PRAW** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- The data comes from a `RedditSource`: the synthetic generator that ships with
  the project, or the real Reddit API through praw
- Engagement per subreddit, with the averages, and the most active authors
- A sentiment score for every post and every comment, with VADER, so a
  negation is understood
- The comments are analysed as well: the sentiment, the most active
  commenters and the depth of the threads
- Every run is appended to the database with the time it ran, so the history
  of the runs can be read back
- An activity chart and an engagement chart

## StackStack

`Python; PRAW; SQLite; Streamlit`

The CSV stack is PRAW + SQLite + Streamlit. PRAW needs Reddit API credentials and Streamlit is not installed, so this build uses generated posts, SQLite and Flask.

## Run

```bash
pip install -r requirements.txt
python main.py run
python app.py
python main.py demo
pytest -q
```

## Structure

```text
reddit-social-media-analytics-with-praw/
├── main.py                 pipeline CLI
├── src/pipeline.py         data pipeline
├── tests/test_pipeline.py  smoke test
├── requirements.txt
├── app.py                  Flask analytics dashboard
```

## Testing

```bash
pytest -q
```

12 tests: the pipeline runs, the sentiment (a negation changes the sign, the
label, the lexicon fallback), the definition of the engagement, the subreddit
table with the averages, the comments, the authors, the history of the runs
and the source being swappable.

## Notes and limitations

- No Reddit API is called; all posts and comments are synthetic.
- Sentiment uses a small positive/negative word list, not a trained model.
- The dashboard is read-only and has no live refresh.

## License

BSD-3-Clause. See `LICENSE`.

## About the scope

This is a third-year student project, not a production data platform. It uses local files and SQLite so the pipeline can run on one machine. The notes above list the production pieces that were replaced or skipped.
