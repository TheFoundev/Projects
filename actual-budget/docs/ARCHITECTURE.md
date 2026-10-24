# Architecture

Two runtimes, one domain model.

```
Browser (React)                 Node.js
───────────────                 ───────
views/  ── reads/writes ──▶     api/        HTTP handlers
  ▲          store.js             │
  │            │                  ▼
  │            ▼              domain/       pure functions
  │         IndexedDB ◀──▶ sync.js          budget maths, rules,
  │                                │         schedules, reports
  └──────── render ◀───────────────┘
                            SQLite (node:sqlite)
```

## Why this split

- **`server/domain/`** contains no I/O. Given plain rows it returns plain
  objects. That makes the budget maths, rule matching, schedule arithmetic and
  report aggregation directly unit-testable without a database or a browser.
- **`server/api/`** owns HTTP concerns only: parse, validate, call domain,
  persist, serialise. Handlers receive a `ctx` (`{ db, params, query, body }`).
- **`client/lib/store.js`** is the single source of truth for the UI. Views
  subscribe; nothing renders from `fetch` directly.
- **`client/lib/sync.js`** is the only place that talks to the network.

## Local-first model

Every synced row carries `updated_at` (ISO 8601) and a soft-delete flag
`deleted` (0/1). Nothing is ever hard-deleted over the wire, so a delete
propagates like any other change.

A mutation follows this path:

1. The view calls a store action (`store.addTransaction(tx)`).
- The store writes the row into **IndexedDB** with a fresh `updated_at` and
  `dirty = 1`, updates in-memory state, and notifies subscribers. The UI
  updates immediately — this is the *local-first* part.
- The mutation is appended to a **pending queue** in IndexedDB.
- The sync loop:
  1. `POST /api/sync/push` with the queued rows (batched).
  2. On success, clears the queue entries and marks the rows clean.
  3. `GET /api/sync/pull?since=<server time of last pull>` and merges the
     returned rows into IndexedDB.

## Conflict resolution

Last-write-wins **per row**, comparing `updated_at` (ISO-8601, UTC). The
comparison lives in one place on each side:

- Server: `applyIncoming()` in `server/api/sync.js` — an incoming row is
  applied only when `incoming.updated_at > stored.updated_at`.
- Client: `merge()` in `client/lib/store.js` — same rule.

LWW is deliberately simple. It is the right trade-off for a single-user
budget that syncs between their own devices; it is *not* a multi-writer CRDT,
and the docs say so rather than pretending otherwise.

## The budget chain

`available` is recursive: a category's available this month is last month's
available plus what you budgeted plus what you spent. `computeBudgetThrough()`
therefore walks forward from the earliest month that has any activity, so the
history is consistent no matter which month you open.

Incomes are transactions whose category belongs to an income group.
`to_be_budgeted` accumulates the same way: `tbb(month) = tbb(prev) + income −
budgeted`.

## Bank sync

Real bank aggregation needs a provider (Plaid, GoCardless, ...) and
credentials. Inventing those would be dishonest, so the seam is explicit:

- `GET /api/bank/providers` reports which (if any) are configured — by default
  an empty list, and the UI says "no providers configured".
- `POST /api/import/csv` implements the part that genuinely works offline:
  parse a CSV export, detect duplicates by a content hash, and let the user
  categorise. Rules then auto-assign categories on import.

Adding a provider means implementing the same output shape and registering it
in `server/api/bank.js`; nothing else changes.

## No build step

The client is plain ES modules loaded by the browser. React and htm are
vendored UMD/UMD-style bundles; `client/lib/htm.js` binds `htm` to
`React.createElement`, so views read like JSX:

```js
import { html } from '../lib/htm.js';
export const View = () => html`<h1>Budget</h1>`;
```

This keeps the project inspectable: what you read is what the browser runs.
