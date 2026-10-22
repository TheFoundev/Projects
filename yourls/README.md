# YOURLS

Short links with simple click stats

> Self-hosted URL shortener with custom keywords, click statistics, plugins, an API and a bookmarklet for generating links.

## Overview

An original, self-contained implementation of the **YOURLS** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Create short links with custom slugs
- Redirect endpoint with click counting
- Tags and titles for organisation
- Search across saved links
- Owner/member accounts

## Stack

`PHP`
The application follows a small MVC structure (front controller, PDO models, PHP views) and uses PDO so the same code runs on SQLite locally and MySQL in production.

## Run

```bash
php -S localhost:8000 -t public
# open http://localhost:8000
```

## Structure

```text
yourls/
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

The suite has no external dependency: the tests run against a SQLite database
of their own.


## Notes and limitations

- Visit /r/<slug> to use a short link; each redirect increments its click counter.
- No custom-domain DNS setup or QR generation in this version.
- The original YOURLS is PHP/MySQL; this build uses PHP + PDO with SQLite for easy local setup.

## License

MIT. See `LICENSE`.
