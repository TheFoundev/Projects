# Roadmap

A build order for the project, split into milestones. Each milestone ends with
something demonstrable.

## M0 — Foundations

- [x] SQLite schema with sync columns (`updated_at`, `deleted`)
- [x] Money as integer cents; parse/format helpers
- [x] HTTP server, JSON helpers, router with `:params`
- [x] Static asset serving (client + vendor)

## M1 — Core budget

- [x] Accounts CRUD, on/off budget
- [x] Category groups and categories
- [x] Transactions CRUD
- [x] Monthly budget: budgeted / activity / available / carry-over
- [x] To be budgeted accumulation
- [x] Budget UI with inline editing

## M2 — Automation

- [x] Rule engine and rules UI
- [x] Rules applied on CSV import
- [x] Scheduled transactions, upcoming list, posting

## M3 — Insight

- [x] Goals with progress
- [x] Net worth over time
- [x] Spending by category
- [x] Income vs expense cash flow

## M4 — Local-first

- [x] IndexedDB mirror of every syncable table
- [x] Optimistic writes + pending queue
- [x] Push/pull sync with last-write-wins
- [x] Offline indicator and pending count

## M5 — Import & adapters

- [x] CSV import with duplicate detection
- [x] Provider seam (`/api/bank/providers`), honest "none configured" state
- [ ] A concrete provider adapter (needs real credentials — out of scope here)

## M6 — Hardening

- [x] `node:test` coverage for domain, API and sync
- [ ] Multi-user accounts and server-side auth
- [ ] Attachments on transactions
- [ ] Reconcile workflow (lock cleared transactions)
- [ ] Mobile layout polish

## Known limitations (honest list)

- Sync is last-write-wins per row, not a CRDT. Two devices editing the *same
  row* at the same second will lose the older edit. Acceptable for one person's
  budget across their own devices; documented rather than hidden.
- No authentication: the server assumes a single trusted user on localhost.
  Do not expose it to the internet as-is (see M6).
- Bank aggregation is a seam, not an integration: no provider is configured by
  default and none is faked.
- Transfers are modelled as two linked transactions; editing one leg does not
  rewrite the other.
