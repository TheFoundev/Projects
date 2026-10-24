# Chatwoot

Every support conversation in one inbox

> Customer support platform with shared inboxes, a live chat widget, email channels, canned responses and reporting.

## Overview

An original, self-contained implementation of the **Chatwoot** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Shared inbox with conversation status and priority
- Threaded replies with internal sender attribution
- Canned responses for fast, consistent answers
- Channel and assignee tracking
- Seed conversations so the inbox is usable immediately

## Stack

`Ruby; Rails; Vue; PostgreSQL`

The app intentionally keeps a dependency-free Node stack; SQLite is provided by Node's built-in `node:sqlite` module (Node 22.5+).

## Run

```bash
npm start
# open http://localhost:3000
npm test
```

## Structure

```text
chatwoot/
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

21 tests: the rules of the inbox on their own (states, transitions,
priorities, the thread and its internal notes, the inbox counters and
filters, the round robin, the canned response search) and the API on a real
server (the inbox endpoint, replying, internal notes, changing the status, a
reply reopening a waiting conversation, assigning, the canned response, the
search and the sign-in requirement).

## The helpdesk domain

`helpdesk.js` holds the rules of the inbox, as pure functions:

- the states a conversation can be in (`open`, `pending`, `closed`) and the
  transitions between them, including reopening a closed conversation
- the priority levels and the reply types (`inbound`, `outbound`, `note`)
- the thread of a conversation, with the internal notes counted separately so
  they are never shown to the requester
- the shared inbox: the conversations sorted by priority, with the counters a
  support team looks at first, and filters by state, priority, agent and text
- the round robin that gives the next conversation to the agent with the
  least work
- the canned response search, where a title that matches the query beats one
  that only contains it

The API adds `/api/inbox`, `/api/conversations/:id/thread`,
`/api/conversations/:id/messages`, `/api/conversations/:id/status`,
`/api/conversations/:id/assign`, `/api/conversations/:id/canned/:cannedId`,
`/api/conversations/:id/events` and `/api/canned_responses/search`.

## Notes and limitations

- The inbox is a focused MVP: shared statuses, replies and canned responses; email/chat channel integrations are represented as data rather than live connectors.
- The upstream Chatwoot is Rails + Vue. This runnable implementation uses the Foundev zero-dependency Node stack and keeps the same conversation/message domain model.
- Agent accounts are the app users; assignment is a free-text field rather than a full RBAC roster.

## License

MIT. See `LICENSE`.
