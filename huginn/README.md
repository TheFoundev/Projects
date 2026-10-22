# Huginn

Agents that watch the web for you

> Automation platform of agents that watch events, monitor websites and trigger actions such as alerts, posts or API calls.

## Overview

An original, self-contained implementation of the **Huginn** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Agents with HTTP check, webhook and digest behaviours
- Manual run button with recorded latency and outcome
- Event stream of everything an agent observed
- Run history with error messages
- Schedules and status stored alongside each agent

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
huginn/
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

3 domain tests (`npm test`), on top of the smoke test: the agents, running one and an agent that does not exist.


## Notes and limitations

- Schedules are descriptive metadata; runs are triggered manually (or with your own cron calling the run endpoint).
- HTTP agents perform real outbound GET/POST requests with an 8 second timeout.
- This Foundev MVP keeps the agent/event/run model of Huginn without shipping every upstream agent plugin.

## License

MIT. See `LICENSE`.
