# Thunderdome Planning Poker

Real-time agile collaboration for **planning poker**, **retrospectives** and
**daily standups**. Create a room, share the link, and everyone sees votes and
notes update live.

> Agile collaboration tool for planning poker estimation, sprint retrospectives, daily standups and user story mapping in real time.

## Features

- Planning poker with Fibonacci cards (0, 1, 2, 3, 5, 8, 13, 21, ?)
- Hidden votes until the facilitator reveals, then average and per-person values
- Retrospective columns: went well / improve / actions
- Standup columns: yesterday / today / blockers
- Room codes, shareable links and display-name join (no accounts)
- Server-sent events for live updates
- In-memory store with concurrency-safe mutation and tests

## Stack

`Go; React; PostgreSQL; WebSockets` — this implementation uses Go's standard
library and server-sent events, and a dependency-free browser client. State is
in memory: restarting the server clears rooms, which is intentional for a
workshop tool. The HTTP API is small enough to swap the store for PostgreSQL.

## Run

```bash
go run .
# open http://localhost:8080
go test ./...
```

No external modules are required. Go 1.22+.

## Structure

```text
thunderdome-planning-poker/
├── main.go              HTTP API, session store, SSE hub
├── main_test.go         API flow and validation tests
├── static/index.html    app shell
├── static/app.js        planning poker and retro client
├── static/style.css     responsive styling
└── go.mod
```

## API

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/sessions` | create a room (`name`, `mode`) |
| GET | `/api/sessions/{id}` | read a room |
| POST | `/api/sessions/{id}/join` | join with a display name |
| POST | `/api/sessions/{id}/stories` | add a story |
| POST | `/api/sessions/{id}/vote` | cast an estimate |
| POST | `/api/sessions/{id}/reveal` | reveal the round |
| POST | `/api/sessions/{id}/reset` | clear votes for a new round |
| POST | `/api/sessions/{id}/notes` | add a retro/standup note |
| GET | `/api/sessions/{id}/events` | SSE change stream |

## Notes and limitations

- Sessions live in memory; there is no database persistence in this MVP.
- A facilitator role is not enforced — any participant can reveal or reset.
- User story mapping is represented by the ordered story list, not a separate canvas.
- The upstream is Go + React + PostgreSQL + WebSockets; this Foundev build keeps
  the real-time collaboration core and removes the install step.

## License

Apache-2.0. See `LICENSE`.
