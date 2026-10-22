# Rocket.Chat Mobile

A small team chat client with channels and local messages.

> The official React Native client for the Rocket.Chat open-source team communication platform.

## Overview

An original, self-contained implementation of the **Rocket.Chat Mobile** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- A client that speaks the DDP protocol over a websocket: the connect, the
  calls, the answers, the ping and the messages the server pushes
- The channels and the messages of the server, with the unread counts
- The channels and the messages are kept on the device, so the app shows
  something the moment it opens and keeps working without a connection
- The state of the connection is shown, with a way to try again
- A message that is sent shows up at once and is sent to the server

## Stack

`React Native; TypeScript; Redux; WebSocket`

The CSV stack is React Native + TypeScript + Redux + WebSocket. This build uses local state and mock data; no Rocket.Chat server is contacted.

## Run

```bash
npm install
npm start
# scan the QR code with Expo Go, or press w for web
```

## Structure

```text
rocket-chat-mobile/
├── App.tsx              tab shell
├── src/screens/          one file per screen
├── src/components.tsx    small shared UI pieces
├── src/data.ts           mock data
├── src/theme.ts          colours and spacing
└── app.json / package.json
```

## Testing

```bash
npm test          # node:test, no extra dependencies
npm run typecheck
```

14 tests: the client connects and gets a session, a call answers with the
result of the server, a call without a connection and a call that times out
are refused, the answers of the server are turned into channels and
messages, the unread counts, the ping is answered with a pong and the
messages the server pushes reach the handler.

## Notes and limitations

- Channels and messages live in `src/data.ts` and reset when the app restarts.
- There is no login, real-time sync or push notification integration.
- A real client would connect to a Rocket.Chat server over DDP/WebSocket.

## License

MIT. See `LICENSE`.

## Project notes

This is a student-style portfolio build of the core idea, not a production
client. The UI is deliberately small: a tab shell, themed screens and mock
data. It should run in Expo Go after `npm install`.

Things that are mocked or simplified are listed below so the scope is clear.
