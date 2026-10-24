# COVID Alert

A simple exposure-check and symptom tracker for a class project.

> Canada's exposure-notification app built with React Native and used as an accessibility showcase.

## Overview

An original, self-contained implementation of the **COVID Alert** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Exposure status card with a simulated check
- Symptom checklist with a basic result summary
- Support resources and help lines
- Recent check history

## Stack

`React Native; TypeScript; Exposure Notification; Native modules`

The CSV stack is React Native + TypeScript + Exposure Notification. Real exposure notification needs a native module and public-health keys, so this build simulates checks and stores them on the device.

## Run

```bash
npm install
npm start
# scan the QR code with Expo Go, or press w for web
```

## Structure

```text
covid-alert/
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

20 tests: the simulated exposure service, the check history and the "next
check due" calculation, the symptom scoring model and its risk levels, and
the persistence layer (including a corrupt saved value and a backend that
fails).

## Notes and limitations

- Exposure checks are simulated; no Bluetooth or Google/Apple EN API is used.
- The symptom result is informational only and is not medical advice.
- Check history lives in component state and resets when the app restarts.

## License

Apache-2.0. See `LICENSE`.

## Project notes

This is a student-style portfolio build of the core idea, not a production
client. The UI is deliberately small: a tab shell, themed screens and mock
data. It should run in Expo Go after `npm install`.

Things that are mocked or simplified are listed below so the scope is clear.

- Not a medical device and not connected to any health authority.
- A production build would need native permissions, key servers and privacy review.
