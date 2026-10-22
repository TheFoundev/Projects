# Signal-style E2EE Chat

A chat relay where the server only sees encrypted envelopes.

> An educational end-to-end encrypted chat that implements core Signal Protocol ideas over WebSockets.

## Overview

An original, self-contained implementation of the **Signal-style E2EE Chat** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- X25519 key exchange with HKDF-derived session keys
- AES-256-GCM encryption with authenticated tags
- Hand-rolled WebSocket relay that forwards opaque envelopes
- Browser client that shares a room passphrase for end-to-end encryption

## Stack

`Node.js`
The CSV stack is Node.js.js + WebSockets + libsignal. libsignal is not available, so the project uses node:crypto X25519 and AES-GCM; it is not the Signal protocol and there is no double ratchet.

## Run

```bash
npm start
npm test
```

## Structure

```text
signal-style-e2ee-chat/
├── src/crypto.js           X25519 and AES-GCM helpers
├── src/ws.js               minimal WebSocket server
├── src/server.js            static files and the relay
├── public/index.html        chat page
├── public/app.js            browser key derivation and encryption
├── test/                    crypto and relay tests
└── package.json
```

## Testing

```bash
# see the Run section
```

## Notes and limitations

- There is no forward secrecy per message, prekey bundle or group session.
- The room passphrase is typed into the browser; key distribution is manual.
- The relay keeps no history and stores nothing, but it is not audited.

## License

Apache-2.0. See `LICENSE`.

## About the scope

This is a third-year student project. It targets Node's built-in modules and has no third-party runtime dependencies, so a few upstream conveniences are missing.
