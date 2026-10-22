# Sniffnet

Summarise a packet capture from a simple CSV trace.

> A cross-platform network traffic monitor written in Rust that makes packet capture approachable and visual.

## Overview

An original, self-contained implementation of the **Sniffnet** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Capture records parsed from source, destination, protocol and bytes
- Per-protocol byte totals
- Top talkers ranked by bytes
- Library API with unit tests and a small CLI

## Stack

`Rust`
The CSV stack is Rust. This build has no external crates, so it reads a small CSV trace format instead of a live pcap device, and prints a terminal summary instead of a GUI.

## Run

```bash
cargo run --release
cargo test --offline
```

## Structure

```text
sniffnet/
├── src/lib.rs            capture parsing and statistics
├── src/main.rs           command line summary
└── Cargo.toml
```

## Testing

```bash
cargo test
```

7 tests (`cargo test`), up from 3.


## Notes and limitations

- There is no live capture, network interface access or GUI.
- The parser expects four comma-separated fields per line.
- Statistics are simple totals, not time-series or flow analysis.

## License

MIT. See `LICENSE`.

## About the scope

This is a third-year student project in Rust with no external crates. It is not a production implementation; the notes list what was skipped.
