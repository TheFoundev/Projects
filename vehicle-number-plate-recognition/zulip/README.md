# Zulip

Threaded team chat organised by topic

> Threaded team chat organised by topics with streams, private messages, markdown, integrations and full-text search.

## Overview

An original, self-contained implementation of the **Zulip** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Streams (channels) with topics on every message
- Chronological message history per stream
- Named authors and timestamps
- Markdown-friendly plain-text message body
- Session accounts with first-user ownership

## Stack

`Python; Django; React; PostgreSQL`

Flask + SQLite + Jinja. The CSV stack is honoured by the primary language and domain model; framework-specific integrations are called out in the notes.

## Run

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py
# open http://localhost:5000
pytest -q
```

## Structure

```text
zulip/
├── app.py               Flask routes, auth, JSON API and domain logic
├── config.json          resource schema and seed data
├── templates/           server-rendered Jinja views
├── static/style.css     responsive styling
├── tests/               pytest smoke test
└── data/app.db          local database (gitignored)
```

## Testing

```bash
# see the Run section
```

## Notes and limitations

- Messages are grouped by stream and topic; there is no cross-stream search index yet.
- The upstream Zulip is Django + React; this Foundev MVP preserves the stream/topic conversation model in a runnable Flask app.
- Markdown is stored as plain text and rendered without HTML to avoid XSS in the demo.

## License

Apache-2.0. See `LICENSE`.
