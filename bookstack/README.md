# BookStack

Documentation that stays organised

> Documentation wiki that organises pages into shelves, books and chapters with WYSIWYG editing, versioning, search and role permissions.

## Overview

An original, self-contained implementation of the **BookStack** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Books, chapters and pages with a clear hierarchy
- Page editor with automatic revision history
- Full-text search across books, chapters and pages
- Owner/member accounts with session authentication
- Seed content so the wiki is useful on first run

## Stack

`PHP; Laravel; MySQL; JavaScript`

The application follows a small MVC structure (front controller, PDO models, PHP views) and uses PDO so the same code runs on SQLite locally and MySQL in production.

## Run

```bash
php -S localhost:8000 -t public
# open http://localhost:8000
```

## Structure

```text
bookstack/
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

74 assertions in two suites: the rules of the library on their own (the
hierarchy, the book of a page, the tree of a book, the search, the versions
and the revisions, the permissions, the summary, and the database refusing a
chapter without a book) and the app itself on a real server (the library is
created, the hierarchy rules, the search, the book tree, a member editing a
page but not a book, and the revisions).

## The library

`src/wiki.php` holds the rules, as pure functions:

- the hierarchy: a chapter belongs to a book and a page belongs to a chapter,
  and the database refuses a row that breaks it
- the book of a page and the tree of a book, with the chapters in the order
  of their position
- the search across the books, the chapters and the pages at once
- the version a page goes to when it is saved, and the revision that is
  written with it
- the permissions: the owner can do everything, a member can read the library
  and edit the pages, and nobody else can delete anything

The app has a search at `/search`, a book tree at `/books/{id}` and the
library summary on the dashboard.

## Notes and limitations

- The page editor is a plain-text/Markdown textarea; there is no bundled WYSIWYG editor dependency.
- Page revisions are recorded automatically on every edit, with version numbers.
- SQLite is the zero-config database; the PDO schema can be ported to MySQL for the upstream deployment shape.
- Roles are intentionally simple: the first account is the owner, later accounts are members.

## License

MIT. See `LICENSE`.
