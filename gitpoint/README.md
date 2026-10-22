# GitPoint

A small GitHub client for browsing repos and issues.

> A polished React Native GitHub client with issues, notifications, profiles and repository browsing.

## Overview

An original, self-contained implementation of the **GitPoint** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- A client for the GitHub REST API: the repositories of a user, the issues of
  a user and a profile, with the rate limit of the answer
- The data is kept on the device, so the app shows something the moment it
  opens and keeps working without a network
- The seed data is the last fallback when the API cannot be reached
- A search over the repositories, and a filter over the state of the issues
- The rate limit of the API is shown, so it is clear when it runs out

## Stack

`React Native; Redux; GitHub API`

The CSV stack is React Native + Redux + GitHub API. This build skips Redux and uses local state plus mock data so it runs without a token or network.

## Run

```bash
npm install
npm start
# scan the QR code with Expo Go, or press w for web
```

## Structure

```text
gitpoint/
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

16 tests: the client (the repositories, the issues, the rate limit, the
errors), the turning of the answer into the types the screens use, the
sorting, the searches and the cache (including a corrupt value and a storage
that fails).

## Notes and limitations

- Repositories, issues and the profile are mock data in `src/data.ts`.
- A real client would call the GitHub REST API and handle pagination and rate limits.
- No authentication, notifications or code browsing in this version.

## License

MIT. See `LICENSE`.

## Project notes

This is a student-style portfolio build of the core idea, not a production
client. The UI is deliberately small: a tab shell, themed screens and mock
data. It should run in Expo Go after `npm install`.

Things that are mocked or simplified are listed below so the scope is clear.
