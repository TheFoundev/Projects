# Ghost

Publishing, members and newsletters

> Publishing platform for professional blogs and newsletters with a content editor, memberships, subscriptions and themes.

## Overview

An original, self-contained implementation of the **Ghost** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Post editor with draft and published states
- Public blog view for published posts
- Member records with plan and status
- Newsletter issue tracking
- Searchable content API

## Stack

`Node.js; MySQL; Handlebars; REST API`

The app intentionally keeps a dependency-free Node stack; SQLite is provided by Node's built-in `node:sqlite` module (Node 22.5+).

## Run

```bash
npm start
# open http://localhost:3000
npm test
```

## Structure

```text
ghost/
├── server.js          HTTP API, auth and SQLite schema
├── config.json        domain model and seed data
├── public/            dependency-free single-page client
├── test/smoke.test.js API smoke test
└── data/app.db        local database (gitignored)
```

## Testing

```bash
npm test
```

21 tests: the rules of the blog on their own (the post states and their
transitions, the slug rules, what is on the public blog, the draft state, the
content search, the member summary and the newsletter content) and the API on
a real server (a draft with the configured defaults, publishing, the public
blog, the content search, the free slug, the member summary, sending an issue
and sending it twice).

## The blog domain

`blog.js` holds the rules, as pure functions:

- the states a post can be in (`draft`, `published`, `scheduled`,
  `archived`) and the transitions between them, so a published post cannot
  quietly go back to a draft
- the slug rules, including a free slug for a title that is taken
- what the public blog shows: published posts, newest first, and only the
  ones whose date has passed
- the content search over the title, the excerpt and the body
- the member summary by plan and by state
- the content of a newsletter issue: the published posts that were not sent
  yet

The API adds `/api/blog`, `/api/blog/search`,
`/api/posts/:id/publish`, `/api/posts/:id/slug`, `/api/members/summary`,
`/api/newsletters/:id/content` and `/api/newsletters/:id/send`.

## Notes and limitations

- The public blog renders published posts; the editor is a plain-text/Markdown textarea rather than a rich-text card editor.
- Subscriptions are modelled as member plans and newsletter status, without a payment processor integration.
- Upstream Ghost is a Node publishing platform; this runnable Foundev MVP keeps the same zero-install philosophy.

## License

MIT. See `LICENSE`.
