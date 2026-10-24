# BlueWallet

A demo Bitcoin wallet UI with send and receive screens.

> A Bitcoin and Lightning wallet for iOS and Android built with React Native.

## Overview

An original, self-contained implementation of the **BlueWallet** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Wallet overview with balance and recent transactions
- Show/hide balance toggle
- Receive screen with a sample address and copy button
- Send form that validates the address against the bech32 rules, builds an
  unsigned transaction from the wallet's unspent outputs and estimates the fee
- A wallet core interface with two implementations: the offline demo wallet
  and a real Electrum client

## Stack

`React Native; TypeScript; Bitcoin; Electrum`

The CSV stack is React Native + TypeScript + Bitcoin + Electrum.

The stack line in the brief is the target, not the current state. What this
build has:

| Piece | State |
|---|---|
| SHA-256 | implemented in `src/sha256.ts` (no native module needed) |
| bech32 address validation | implemented in `src/address.ts`, BIP-173 |
| Script hash for Electrum | implemented, matches the reference implementation |
| UTXO selection and fee estimation | implemented in `src/wallet-core.ts` |
| Electrum client | implemented, JSON-RPC over a websocket |
| Key handling and signing | **not** implemented |
| Broadcasting | implemented in the client, not exercised by the demo wallet |

## Run

```bash
npm install
npm start
# scan the QR code with Expo Go, or press w for web
```

## Structure

```text
bluewallet/
├── App.tsx              tab shell
├── src/screens/          one file per screen
├── src/components.tsx    small shared UI pieces
├── src/wallet-core.ts    the wallet interface, the demo wallet and the Electrum client
├── src/address.ts        bech32 decoding and the script hash
├── src/sha256.ts         SHA-256 in plain TypeScript
├── src/store.ts          persistence, behind a key/value interface
├── src/persistence.ts    wires the store to AsyncStorage and the websocket
├── src/walletContext.tsx shares the wallet between the screens
├── src/data.ts           the demo transactions
├── src/theme.ts          colours and spacing
├── test/                 the test suite
└── app.json / package.json
```

## Testing

```bash
npm install
npm test          # compiles the suite and runs it
npm run typecheck
```

34 tests: the SHA-256 implementation is checked against the reference
implementation in Node's crypto module, the bech32 decoder is checked against
the BIP-173 vectors, the script hash is checked against an independently
computed value, the transaction builder is checked for bad addresses, bad
amounts and insufficient funds, and the Electrum client is checked against a
fake transport.

## Notes and limitations

- The demo wallet has no keys, so it records a payment locally instead of
  signing and broadcasting it. The Electrum client can broadcast, but the
  demo wallet does not use it.
- There is no key storage, no signing and no Lightning support.
- The address on the receive screen is a placeholder. Do not send real
  Bitcoin to it.

## License

MIT. See `LICENSE`.

## Project notes

This is a student-style portfolio build of the core idea, not a production
client. The UI is deliberately small: a tab shell, themed screens and mock
data. It should run in Expo Go after `npm install`.

Things that are mocked or simplified are listed below so the scope is clear.

- Do not send real Bitcoin to the address shown; it is a placeholder.
- No QR scanner and no transaction history sync.
