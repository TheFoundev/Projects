# Actual Budget

A **local-first envelope budgeting app**. Accounts, envelope categories, a
monthly budget, rules, scheduled transactions, goals and net-worth reports —
working offline and syncing when it can.

Built as a Foundev project. The API contract was inspired by the open-source
budgeting space; the code here is original (see [LICENSE](LICENSE) and
`docs/ROADMAP.md`).

## Why local-first

The browser is the source of truth for the UI. Every edit is written to
**IndexedDB first**, rendered immediately, and queued. A background sync loop
pushes the queue to the server and pulls other devices' changes. Go offline
mid-budget and nothing blocks: the badge in the header shows `offline` and the
number of pending edits.

## Run it

```bash
node server/seed.js     # optional: create data/budget.db with a demo budget
node server/index.js    # http://localhost:8787
```

No `npm install` required — the project has **zero runtime dependencies**.
React and htm are vendored in `vendor/` under their own licences.

| Command | Does |
|---|---|
| `npm start` | run the server |
| `npm run seed` | (re)create the demo database |
| `npm test` | run the `node:test` suite (domain, API and sync) |

The suites are `test/domain.test.js` (pure logic), `test/api.test.js` (the real
HTTP API against a seeded in-memory database) and `test/sync.test.js` (the
sync engine, the merge rule and the offline behaviour).

Environment: `PORT` (default `8787`), `FOUNDEV_DB` (default `data/budget.db`,
use `:memory:` for throwaway runs).

## Features

- **Envelope budgeting** — per-category *Budgeted / Activity / Available* with
  carry-over and a running **To be budgeted** figure.
- **Accounts** — on-budget and tracking, assets and liabilities.
- **Transactions** — payee, memo, category, cleared flag, transfers.
- **Rules** — auto-categorise by payee/memo/amount.
- **Schedules** — recurring transactions with an upcoming list and posting.
- **Goals** — target balance by date, and the monthly amount needed.
- **Reports** — net worth over time, spending by category, cash flow.
- **CSV import** — with duplicate detection.
- **Offline sync** — the mirror is written first, edits are queued, and the
  queue is pushed and pulled with last-write-wins reconciliation by
  `updated_at`. The header badge shows the connection state and the number of
  pending edits.
- **Editable budget** — click a budgeted amount to change it.
- **Transaction editing** — add, recategorise, delete and record transfers
  between two accounts.
- **CSV import preview** — run the import as a dry run first and see what
  would be added, what was already imported and what was skipped.

## How the client works

The browser holds the truth for the UI. Four small modules make that work:

| File | Does |
|---|---|
| `client/lib/store.js` | the local mirror. `IndexedDbStore` in the browser, `MemoryStore` for the tests and as the fallback when IndexedDB is unavailable. |
| `client/lib/sync.js` | `SyncEngine`: push the queue, pull the changes, merge last-write-wins by `updated_at`. |
| `client/lib/data.js` | `DataLayer`: reads go to the server and fall back to the mirror, writes go to the mirror and the queue first. |
| `client/lib/api.js` | one place that knows the URL shapes. |

A write made while offline lands in the mirror, is rendered immediately and
stays in the queue until the server takes it. The badge in the header shows
`offline` and the number of pending edits; clicking it syncs.

## Layout

```
actual-budget/
├── server/            Node HTTP API + SQLite
│   ├── domain/        pure logic (budget, rules, schedules, reports)
│   └── api/           route handlers
├── client/            React app (ES modules, no bundler)
│   └── lib/           store, sync engine, data layer, API client
├── vendor/            React, ReactDOM, htm (unmodified)
├── test/              node:test suites (domain, API, sync)
└── docs/              architecture, data model, API, roadmap
```

Design notes: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) ·
[`docs/API.md`](docs/API.md) · [`docs/DATA-MODEL.md`](docs/DATA-MODEL.md)

## Money

All amounts are **integer cents**. Nothing is stored as a float, so
`0.1 + 0.2` can never leak into a balance.

## Licence

MIT. React, ReactDOM and htm are vendored unmodified under their own licences
(see `vendor/`).
