# Rocket.Chat

Team chat with channels and live updates

> Team communication platform with channels, direct messages, threads, file sharing, webhooks, bots and video conferencing.

## Overview

An original, self-contained implementation of the **Rocket.Chat** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Channels with topics and membership metadata
- Real-time message updates over server-sent events
- Persistent message history
- Named authors and timestamps
- Direct-message-ready channel model

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
rocket-chat/
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

4 domain tests (`npm test`), on top of the smoke test: the channels, sending a message and the stream of the events.


## Notes and limitations

- Real-time delivery uses server-sent events instead of Meteor's DDP; the user-facing behaviour (new messages appear live) is preserved.
- File sharing, bots and video calls are out of scope for this focused chat MVP.
- The upstream Rocket.Chat is Node/Meteor; this Foundev implementation is dependency-free Node.

## License

MIT. See `LICENSE`.
