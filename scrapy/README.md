# Scrapy

A small breadth-first crawler over a locally served site.

> A fast crawling framework used to build polite web spiders that scope authorised reconnaissance targets.

## Overview

An original, self-contained implementation of the **Scrapy** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Generated test site served on localhost
- HTML parser for titles, links and paragraphs
- Breadth-first crawl with a depth limit
- JSONL page index and broken-link report

## Stack

`Python`
The CSV stack is Python. Scrapy and Twisted are not installed, so this build uses urllib, html.parser and the standard library HTTP server.

## Run

```bash
pip install -r requirements.txt
python main.py run
python main.py demo
pytest -q
```

## Structure

```text
scrapy/
├── main.py                 pipeline CLI
├── src/pipeline.py         data pipeline
├── tests/test_pipeline.py  smoke test
├── requirements.txt
```

## Testing

```bash
pytest -q
```

6 tests (`pytest -q`), up from 2: the crawl, the depth, the limit and the broken links.


## Notes and limitations

- There is no scheduler, retry middleware, robots.txt handling or CSS selector language.
- The crawl target is a generated local site.
- Only same-host links are followed.

## License

BSD-3-Clause. See `LICENSE`.

## About the scope

This is a third-year student project, not a production data platform. It uses local files and SQLite so the pipeline can run on one machine. The notes above list the production pieces that were replaced or skipped.
