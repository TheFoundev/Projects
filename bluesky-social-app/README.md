# Bluesky Social App

A small social feed built on the AT Protocol idea.

> The official Bluesky social app for iOS, Android and web with custom feeds and the AT Protocol.

## Overview

An original, self-contained implementation of the **Bluesky Social App** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Home feed with likes and a local composer
- Discover tab with suggested feeds and topics
- Profile with bio, stats and your posts
- Everything you write or like is saved on the device and survives a restart

## Stack

`React Native; Expo; TypeScript; AT Protocol`

The CSV stack is React Native + Expo + TypeScript + AT Protocol. This build keeps the mobile UI and feed model; posts are local mock data rather than live AT Protocol records.

## Run

```bash
npm install
npm start
# scan the QR code with Expo Go, or press w for web
```

## Structure

```text
bluesky-social-app/
├── App.tsx              tab shell
├── src/screens/          one file per screen
├── src/components.tsx    small shared UI pieces
├── src/feed.ts           the feed model, pure functions
├── src/store.ts          persistence, behind a key/value interface
├── src/persistence.ts    wires the store to AsyncStorage
├── src/feedContext.tsx   shares the feed between the screens
├── src/data.ts           seed data
├── src/theme.ts          colours and spacing
├── test/                 node:test suites
└── app.json / package.json
```

## Testing

```bash
npm test        # node:test, no extra dependencies
npm run typecheck
```

The suite covers the feed model (`src/feed.ts`: publishing, likes, topic
filtering, merging remote posts, the profile counters) and the persistence
layer (`src/store.ts`: round-tripping the state, a corrupt saved value and a
storage backend that fails).

## Notes and limitations

- The feed is seeded in `src/data.ts`; there are still no real AT Protocol
  network calls. `src/feed.ts` has the merge function a network layer would
  call, so the client code is ready for one.
- Publishing and likes are saved on the device with AsyncStorage, so they
  survive a restart. There is no server to sync them with yet.
- No login, moderation or real AT Protocol network calls yet.

## License

MIT. See `LICENSE`.

## Project notes

This is a student-style portfolio build of the core idea, not a production
client. The UI is deliberately small: a tab shell, themed screens and mock
data. It should run in Expo Go after `npm install`.

Things that are mocked or simplified are listed below so the scope is clear.
