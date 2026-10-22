# VPN and Virtual Switch

A UDP tunnel with AES-GCM packets and a virtual switch.

> A tutorial that builds a Layer 2 virtual switch and VPN overlay similar to ZeroTier.

## Overview

An original, self-contained implementation of the **VPN and Virtual Switch** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- The key is derived with PBKDF2 and a random salt, so the same passphrase
  gives a different key on every machine
- Every packet carries a sequence number that is authenticated with the
  ciphertext, and a replay guard refuses a packet that was seen before or
  that is older than the last one
- A packet that was changed on the way is refused by the AEAD tag
- The switch routes the packets between the peers

## Stack

`Go`
The CSV stack is Go. This build implements the tunnel and switch in Go over real UDP sockets; there is no TUN device, routing table or C data path.

## Run

```bash
go run . -message hello
go test ./...
```

## Structure

```text
vpn-and-virtual-switch/
├── main.go                tunnel demo
├── vpn.go                 encryption and switch
├── vpn_test.go            unit tests
└── go.mod
```

## Testing

```bash
go test ./...
```

6 tests: the key derivation with a salt, the sequence number of a packet, a
packet that was tampered with, a replay that is refused and the switch that
forwards a packet.

## Notes and limitations

- Keys are derived from a shared passphrase instead of a handshake.
- There is no rekeying, replay window or compression.
- The virtual switch is a userspace map, not a kernel bridge.

## License

MIT. See `LICENSE`.

## About the scope

This is a third-year student project written in Go with the standard library only. It is not a hardened production service; the notes above list the missing pieces.
