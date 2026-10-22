# New Expensify

Expense reports and team chat in one small mobile app.

> New Expensify's React Native codebase for financial collaboration, expense reports and chat.

## Overview

An original, self-contained implementation of the **New Expensify** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- The rules of a report: the states it can be in, the moves between them, the
  checks before an expense is added and before a report is submitted
- A large report needs a reason before it is submitted
- The expenses are grouped by category, with the totals
- The reports, the chat and the settings are kept on the device, so they are
  still there after a restart
- Submitting a report really moves it, and the button says what happened

## Stack

`React Native; TypeScript; Jest; REST`

The CSV stack is React Native + TypeScript + Jest + REST. This build keeps the mobile expense/chat flows; there is no REST server and no Jest suite.

## Run

```bash
npm install
npm start
# scan the QR code with Expo Go, or press w for web
```

## Structure

```text
new-expensify/
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

18 tests: the states of a report and the moves between them, the totals, the
grouping by category, the checks of an expense and of a report, the filters,
adding and removing an expense, moving a report, the search in the chat and
the store (including a corrupt value and a storage that fails).

## Notes and limitations

- Reports, expenses and chat messages are mock data in `src/data.ts`.
- New chat messages are local to the session and disappear on restart.
- There is no authentication, payment, receipt OCR or real sync.

## License

MIT. See `LICENSE`.

## Project notes

This is a student-style portfolio build of the core idea, not a production
client. The UI is deliberately small: a tab shell, themed screens and mock
data. It should run in Expo Go after `npm install`.

Things that are mocked or simplified are listed below so the scope is clear.
