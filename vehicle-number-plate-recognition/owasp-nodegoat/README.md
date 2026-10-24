# OWASP NodeGoat

A deliberately insecure web app for practising OWASP-style attacks.

> A deliberately insecure Node.js application for learning server-side JavaScript security through guided tutorials.

## Overview

An original, self-contained implementation of the **OWASP NodeGoat** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Login with weak default credentials and a forgeable role cookie
- Search endpoint with a simulated injection flaw
- Unescaped reflected and stored input for XSS practice
- Broken access control on user and admin endpoints

## Stack

`Node.js`
The CSV stack is Node.js.js + Express + MongoDB. This build uses only node:http and in-memory arrays so it runs without a database; the vulnerabilities are kept on purpose.

## Run

```bash
npm start
npm test
```

## Structure

```text
owasp-nodegoat/
├── src/app.js              intentionally vulnerable routes
├── src/store.js            in-memory users and comments
├── src/server.js           server entry point
├── test/app.test.js        checks for each flaw
└── package.json
```

## Testing

```bash
# see the Run section
```

## Notes and limitations

- This app is intentionally insecure. Never expose it to a network.
- It is a teaching target, not a template for real applications.
- Persistence is in memory and resets when the process exits.

## License

Apache-2.0. See `LICENSE`.

## About the scope

This is a third-year student project. It targets Node's built-in modules and has no third-party runtime dependencies, so a few upstream conveniences are missing.
