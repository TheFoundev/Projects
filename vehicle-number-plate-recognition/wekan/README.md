# Wekan

A fast kanban board for real work

> Open-source kanban board with boards, lists, cards, checklists, labels, due dates, file attachments and real-time collaborative updates.

## Overview

An original, self-contained implementation of the **Wekan** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Boards, lists and cards with ordering
- Move cards between lists without a page reload
- Assignees, due dates and free-form notes
- Board visibility and ownership metadata
- Seeded product board so the UI is useful immediately

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
wekan/
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

4 domain tests (`npm test`), on top of the smoke test: the boards, moving a card and the board of somebody else.


## Notes and limitations

- Cards move through a list selector rather than drag-and-drop; ordering is persisted by the move endpoint.
- Real-time multi-user cursors and Meteor subscriptions are not included; the board refreshes on each action.
- Attachments, checklists and swimlanes are out of scope for this MVP. The upstream is Meteor/Node/MongoDB; this build is dependency-free Node + SQLite.

## License

MIT. See `LICENSE`.
