# Wallabag

Save it, read it, keep what matters

> Read-it-later service that saves articles and pages, extracts clean readable content, then supports tags, annotations, search and exports.

## Overview

An original, self-contained implementation of the **Wallabag** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Reading library with unread-first ordering
- Article reader with original-source links
- Quote-level annotations and notes
- Tag and search support across saved articles
- Archive workflow and owner/member accounts

## Stack

`PHP; Symfony; MySQL; JavaScript`

The application follows a small MVC structure (front controller, PDO models, PHP views) and uses PDO so the same code runs on SQLite locally and MySQL in production.

## Run

```bash
php -S localhost:8000 -t public
# open http://localhost:8000
```

## Structure

```text
wallabag/
├── public/index.php     front controller (PHP built-in server router)
├── routes.php           HTTP routes and controllers
├── src/                 PDO database layer, helpers, bootstrap
├── views/               server-rendered templates
├── config.php           resources, seed data and DSN
└── data/app.sqlite      local database (gitignored)
```

## Testing

```bash
composer test      # or: php tests/run.php
```

59 assertions in two suites: the rules of the list on their own (the states,
the rules for an article and an annotation, the tags, the filters, the
counters, the tag cloud, the site of a url and the excerpt) and the app itself
on a real server (an article is saved with its site and its date filled in, an
article without a url is refused, the reading list, the filters, the search
and the annotations).

## The reading list

`src/reader.php` holds the rules, as pure functions:

- the states of an article: unread, read, starred and archived
- the rules for an article: it needs a title, an http url and a site, and
  the site is filled in from the url when it was not given
- the rules for an annotation: it belongs to an article and it has to quote
  something or say something
- the tags of an article and the tag cloud of the list
- the list itself: the filters by state, by tag and by text, and the sorts
  by date, by title and by site
- the counters of the list

The app has the reading list at `/reading`, the annotations of an article at
`/articles/{id}/annotations` and a page extractor at
`/articles/extract`.

## Notes and limitations

- Articles are saved manually (or via the Articles resource); full-text extraction from a URL is not automated in this MVP.
- Annotations are stored separately and shown in the reader; there is no EPUB/Kindle export yet.
- The upstream Wallabag is Symfony; this Foundev build uses the same PHP/PDO MVC shape with SQLite for zero setup.

## License

MIT. See `LICENSE`.
