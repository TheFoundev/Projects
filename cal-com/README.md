# Cal.com

Scheduling without the back-and-forth

> Open scheduling infrastructure with booking pages, availability rules, team round-robin, calendar sync and video conferencing.

## Overview

An original, self-contained implementation of the **Cal.com** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Public booking page with live availability
- Conflict-safe slot reservation backed by SQLite
- Configurable event types and durations
- Downloadable iCalendar export for hosts
- JSON API for event types, availability and bookings

## Stack

`Node.js`
The app intentionally keeps a dependency-free Node stack; SQLite is provided by Node's built-in `node:sqlite` module (Node 22.5+).

## Run

```bash
npm start
# open http://localhost:3000
npm test
```

## Structure

```text
cal-com/
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

5 domain tests (`npm test`), on top of the smoke test: the availability, the calendar and the address of a booking.


## Notes and limitations

- Availability is a single host calendar, Monday–Friday 09:00–17:00 server local time; connect real calendars through the iCal export.
- Video conferencing links and OAuth calendar sync are out of scope for this MVP.
- The CSV stack calls for Next.js/Prisma/PostgreSQL; this runnable MVP uses Node's standard library and SQLite so it starts with zero installs. The API shape maps cleanly onto Next route handlers and a Prisma schema.

## License

MIT. See `LICENSE`.
